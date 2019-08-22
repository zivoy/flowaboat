from enum import Enum
from utils import *
import pyttanko as pytan
import io
from textwrap import wrap
from time import strftime, gmtime, time
import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
import bezier
from PIL import Image
import math

import warnings
from arrow.factory import ArrowParseWarning

warnings.simplefilter("ignore", ArrowParseWarning)

osu_api = Api("https://osu.ppy.sh/api", 60, {"k": Config.credentials.osu_api_key})

parser = pytan.parser()


class MapError(Exception):
    pass


class BadLink(MapError):
    pass


class BadMapFile(MapError):
    pass


class BadId(MapError):
    pass


class NoPlays(UserError):
    pass


class BadMapObject(MapError):
    pass


class NoLeaderBoard(MapError):
    pass


class NoScore(UserError):
    pass


class OsuConsts(Enum):
    # "": 0,
    MODS = {
        "NF": 2 ** 0,
        "EZ": 2 ** 1,
        "TD": 2 ** 2,
        "HD": 2 ** 3,
        "HR": 2 ** 4,
        "SD": 2 ** 5,
        "DT": 2 ** 6,
        "RX": 2 ** 7,
        "HT": 2 ** 8,
        "NC": 2 ** 9,
        "FL": 2 ** 10,
        "AT": 2 ** 11,
        "SO": 2 ** 12,
        "AP": 2 ** 13,
        "PF": 2 ** 14,
        "4K": 2 ** 15,
        "5K": 2 ** 16,
        "6K": 2 ** 17,
        "7K": 2 ** 18,
        "8K": 2 ** 19,
        "FI": 2 ** 20,
        "RD": 2 ** 21,
        "LM": 2 ** 22,
        "TR": 2 ** 23,
        "9K": 2 ** 24,
        "10K": 2 ** 25,
        "1K": 2 ** 26,
        "3K": 2 ** 27,
        "2K": 2 ** 28,
        "V2": 2 ** 29
    }

    R_MODS = {v: k for k, v in MODS.items()}

    DIFF_MODS = ["HR", "EZ", "DT", "HT", "NC", "FL", "HD", "NF"]
    TIME_MODS = ["DT", "HT", "NC"]

    AR_MS_STEP1 = 120
    AR_MS_STEP2 = 150
    AR0_MS = 1800
    AR5_MS = 1200
    AR10_MS = 450
    OD_MS_STEP = 6
    OD0_MS = 79.5
    OD10_MS = 19.5

    DT_SPD = 1.5
    HT_SPD = .75

    HR_AR = 1.4
    EZ_AR = 0.5

    HR_CS = 1.3
    EZ_CS = 0.5

    HR_OD = 1.4
    EZ_OD = 0.5

    HR_HP = 1.4
    EZ_HP = 0.5

    STRAIN_STEP = 400.0
    DECAY_BASE = [0.3, 0.15]
    STAR_SCALING_FACTOR = 0.0675
    EXTREME_SCALING_FACTOR = 0.5
    DECAY_WEIGHT = 0.9


mods_re = regex.compile(rf"^({'|'.join(OsuConsts.MODS.value.keys())})+$")


class Play:
    def __init__(self, play_dict):
        dict_string_to_nums(play_dict)

        self.score = play_dict["score"]
        self.maxcombo = play_dict["maxcombo"]
        self.countmiss = play_dict["countmiss"]
        self.count50 = play_dict["count50"]
        self.count100 = play_dict["count100"]  # + play_dict["countkatu"]
        self.count300 = play_dict["count300"]  # + play_dict["countgeki"]
        self.perfect = play_dict["perfect"]
        self.enabled_mods = parse_mods_string(pytan.mods_str(play_dict["enabled_mods"]))
        self.user_id = play_dict["user_id"]
        self.date = arrow.get(play_dict["date"], date_form)
        self.rank = play_dict["rank"]
        self.accuracy = pytan.acc_calc(self.count300, self.count100, self.count50, self.countmiss)

        if "beatmap_id" in play_dict:
            self.beatmap_id = play_dict["beatmap_id"]
        else:
            self.beatmap_id = 0

        if "replay_available" in play_dict:
            self.replay_available = play_dict["replay_available"]
        else:
            self.replay_available = 0

        if "score_id" in play_dict:
            self.score_id = play_dict["score_id"]
        else:
            self.score_id = ""

        if "pp" in play_dict:
            self.pp = play_dict["pp"]
        else:
            self.pp = None


class CalculateMods:
    def __init__(self, mods):
        self.mods = mods
        if list(mods) != mods:
            self.mods = parse_mods_string(mods)

            Log.log(mods.replace("+", ""))
        Log.log(self.mods)

    def ar(self, raw_ar):
        ar_multiplier = 1

        speed = speed_multiplier(self.mods)

        if "HR" in self.mods:
            ar_multiplier *= OsuConsts.HR_AR.value
        elif "EZ" in self.mods:
            ar_multiplier *= OsuConsts.EZ_AR.value

        ar = raw_ar * ar_multiplier

        if ar <= 5:
            ar_ms = OsuConsts.AR0_MS.value - OsuConsts.AR_MS_STEP1.value * ar
        else:
            ar_ms = OsuConsts.AR5_MS.value - OsuConsts.AR_MS_STEP2.value * (ar - 5)

        if ar_ms < OsuConsts.AR10_MS.value:
            ar_ms = OsuConsts.AR10_MS.value
        if ar_ms > OsuConsts.AR0_MS.value:
            ar_ms = OsuConsts.AR0_MS.value

        ar_ms /= speed

        if ar <= 5:
            ar = (OsuConsts.AR0_MS.value - ar_ms) / OsuConsts.AR_MS_STEP1.value
        else:
            ar = 5 + (OsuConsts.AR5_MS.value - ar_ms) / OsuConsts.AR_MS_STEP2.value

        return ar, ar_ms, self.mods

    def cs(self, raw_cs):
        cs_multiplier = 1

        if "HR" in self.mods:
            cs_multiplier *= OsuConsts.HR_CS.value
        elif "EZ" in self.mods:
            cs_multiplier *= OsuConsts.EZ_CS.value

        cs = min(raw_cs * cs_multiplier, 10)

        return cs, self.mods

    def od(self, raw_od):
        od_multiplier = 1
        speed = 1

        if "HR" in self.mods:
            od_multiplier *= OsuConsts.HR_OD.value
        elif "EZ" in self.mods:
            od_multiplier *= OsuConsts.EZ_OD.value

        if "DT" in self.mods:
            speed *= OsuConsts.DT_SPD.value
        elif "HT" in self.mods:
            speed *= OsuConsts.HT_SPD.value

        od = raw_od * od_multiplier

        odms = OsuConsts.OD0_MS.value - math.ceil(OsuConsts.OD_MS_STEP.value * od)
        odms = min(max(OsuConsts.OD10_MS.value, odms), OsuConsts.OD0_MS.value)

        odms /= speed

        od = (OsuConsts.OD0_MS.value - odms) / OsuConsts.OD_MS_STEP.value

        return od, odms, self.mods

    def hp(self, raw_hp):
        hp_multiplier = 1

        if "HR" in self.mods:
            hp_multiplier *= OsuConsts.HR_HP.value
        elif "EZ" in self.mods:
            hp_multiplier *= OsuConsts.EZ_HP.value

        hp = min(raw_hp * hp_multiplier, 10)

        return hp, self.mods


def parse_mods_string(mods):
    if mods == '' or mods == "nomod":
        return []
    mods = mods.replace("+", "").upper()
    mods_included = mods_re.match(mods)
    if mods_included is None:
        Log.error(f"Mods not valid: {mods}")
        return []  # None
    matches = mods_included.captures(1)
    return list(set(matches))


def sanitize_mods(mods):
    if "NC" in mods and "DT" in mods:
        mods.remove("DT")
    if "PF" in mods and "SD" in mods:
        mods.remove("SD")
    return mods


def speed_multiplier(mods):
    speed = 1
    if "DT" in mods or "NC" in mods:
        speed *= OsuConsts.DT_SPD.value
    elif "HT" in mods:
        speed *= OsuConsts.HT_SPD.value
    return speed


def mod_int(mod_list):
    mod_list = set(mod_list)
    if "NC" in mod_list:
        mod_list.add("DT")
    return pytan.mods_from_str("".join(filter(lambda x: x in OsuConsts.DIFF_MODS.value, mod_list)))


def get_user(user):
    response = osu_api.get('/get_user', {"u": user})
    response = response.json()

    if Config.debug:
        Log.log(response)

    if len(response) == 0:
        raise UserNonexistent(f"Couldn't find user: {user}")

    for i in range(len(response)):
        response[i]["join_date"] = arrow.get(response[i]["join_date"], date_form)
        dict_string_to_nums(response[i])

    return response


def get_leaderboard(beatmap_id, limit=100):
    response = osu_api.get('/get_scores', {"b": beatmap_id, "limit": limit}).json()

    if Config.debug:
        Log.log(response)

    if len(response) == 0:
        raise NoLeaderBoard("Couldn't find leader board for this beatmap")

    for i in range(len(response)):
        response[i]["beatmap_id"] = beatmap_id
        response[i] = Play(response[i])

    return response


def get_user_map_best(beatmap_id, user, enabled_mods=0):
    response = osu_api.get('/get_scores', {"b": beatmap_id, "u": user, "mods": enabled_mods}).json()

    if Config.debug:
        Log.log(response)

    # if len(response) == 0:
    #     raise NoScore("Couldn't find user score for this beatmap")

    for i in range(len(response)):
        response[i] = Play(response[i])
        response[i].beatmap_id = beatmap_id

    return response


def get_user_best(user, limit=100):
    response = osu_api.get('/get_user_best', {"u": user, "limit": limit})
    response = response.json()

    if Config.debug:
        Log.log(response)

    if len(response) == 0:
        raise NoPlays(f"No top plays found for {user}")

    for i in range(len(response)):
        response[i] = Play(response[i])

    return response


def get_user_recent(user, limit=10):
    response = osu_api.get('/get_user_recent', {"u": user, "limit": limit}).json()

    if Config.debug:
        Log.log(response)

    if len(response) == 0:
        raise NoPlays(f"No recent plays found for {user}")

    for i in range(len(response)):
        response[i] = Play(response[i])

    return response


def get_rank_emoji(rank, client):
    if rank == "XH":
        emote = fetch_emote("XH_Rank", None, client)
        return emote if emote else "Silver SS"
    elif rank == "X":
        emote = fetch_emote("X_Rank", None, client)
        return emote if emote else "SS"
    elif rank == "SH":
        emote = fetch_emote("SH_Rank", None, client)
        return emote if emote else "Silver S"
    elif rank == "S":
        emote = fetch_emote("S_Rank", None, client)
        return emote if emote else "S"
    elif rank == "A":
        emote = fetch_emote("A_Rank", None, client)
        return emote if emote else "A"
    elif rank == "B":
        emote = fetch_emote("B_Rank", None, client)
        return emote if emote else "B"
    elif rank == "C":
        emote = fetch_emote("C_Rank", None, client)
        return emote if emote else "C"
    elif rank == "D":
        emote = fetch_emote("D_Rank", None, client)
        return emote if emote else "D"
    elif rank == "F":
        emote = fetch_emote("F_Rank", None, client)
        return emote if emote else "Fail"
    else:
        return False


def get_top(user, index, rb=False, ob=False):
    index = min(max(index, 1), 100)
    limit = 100 if rb or ob else index
    response = get_user_best(user, limit)

    if rb:
        response = sorted(response, key=lambda k: k.date, reverse=True)
    if ob:
        response = sorted(response, key=lambda k: k.date)

    if len(response) < index:
        index = len(response)

    recent_raw = response[index - 1]

    return recent_raw


def get_recent(user, index):
    index = min(max(index, 1), 50)
    response = get_user_recent(user, index)

    if len(response) < index:
        index = len(response)

    recent_raw = response[index - 1]

    return recent_raw


class MapStats:
    def __init__(self, map_id, mods, link_type="id"):
        """
        get stats on map // map api
        :param map_id:
        :param mods: mod **list**
        :param link_type: [id|map|path|url]
        :return: map data dict, map object with calculated values
        """
        if link_type == "id":
            link = f"https://osu.ppy.sh/osu/{map_id}"
        else:
            link = map_id

        if link_type == "map":
            raw_map = link
        elif link_type == "path":
            with open(link, "r") as mp:
                raw_map = mp.read()
        else:
            raw_map = requests.get(link).text
            if raw_map == "":
                raise BadLink

        with io.StringIO(raw_map) as map_io:
            bmp = parser.map(map_io)

        if not bmp.hitobjects:
            raise BadMapFile

        speed = speed_multiplier(mods)

        map_creator = get_user(bmp.creator)[0]
        map_calc = pytan.diff_calc().calc(bmp, mod_int(mods))
        diff = CalculateMods(mods)

        length = bmp.hitobjects[-1].time
        change_list = [i for i in bmp.timing_points if i.change]
        bpm_avg = list()
        bpm_list = list()
        for j, i in enumerate(change_list):
            if i.change:
                if j + 1 == len(change_list):
                    dur = length - i.time
                else:
                    dur = change_list[j + 1].time - i.time
                bpm_avg.append((1000 / i.ms_per_beat * 60) * dur)
                bpm_list.append((1000 / i.ms_per_beat * 60))

        self.speed_multiplier = speed
        self.artist = bmp.artist
        self.title = bmp.title
        self.artist_unicode = bmp.artist_unicode
        self.title_unicode = bmp.title_unicode
        self.version = bmp.version
        self.bpm_min = min(bpm_list) * speed
        self.bpm_max = max(bpm_list) * speed
        self.total_length = (length - bmp.hitobjects[0].time) / 1000 / speed
        self.max_combo = None
        self.creator = bmp.creator
        self.creator_id = map_creator["user_id"]
        self.map_creator = Dict(map_creator)
        self.base_cs = bmp.cs
        self.base_ar = bmp.ar
        self.base_od = bmp.od
        self.base_hp = bmp.hp
        self.cs = diff.cs(bmp.cs)[0]
        self.ar = diff.ar(bmp.ar)[0]
        self.od = diff.od(bmp.od)[0]
        self.hp = diff.hp(bmp.hp)[0]
        self.mode = bmp.mode

        self.hit_objects = len(bmp.hitobjects)
        self.count_normal = bmp.ncircles
        self.count_slider = bmp.nsliders
        self.count_spinner = bmp.nspinners

        if link_type == "id":
            self.approved = 0
            self.submit_date = arrow
            self.approved_date = arrow
            self.last_update = arrow
            self.beatmap_id = 0
            self.beatmapset_id = 0
            self.source = ""
            self.genre_id = 0
            self.language_id = 0
            self.file_md5 = ""
            self.tags = ""
            self.favourite_count = 0
            self.rating = 0.0
            self.playcount = 0
            self.passcount = 0
            self.download_unavailable = 0
            self.audio_unavailable = 0

            mods_applied = mod_int(mods)
            map_web = osu_api.get("/get_beatmaps", {"b": map_id, "mods": mods_applied}).json()
            if not map_web:
                raise BadId
            dict_string_to_nums(map_web[0])
            for i, j in map_web[0].items():
                setattr(self, i, j)
            self.submit_date = arrow.get(self.submit_date, date_form)
            self.approved_date = arrow.get(self.approved_date, date_form)
            self.last_update = arrow.get(self.last_update, date_form)

        try:
            self.leaderboard = get_leaderboard(map_id)
        except NoLeaderBoard:
            self.leaderboard = []

        if self.max_combo is None:
            self.max_combo = bmp.max_combo()
        self.aim_stars = map_calc.aim
        self.speed_stars = map_calc.speed
        self.total = map_calc.total
        self.bpm = sum(bpm_avg) / (length - bmp.hitobjects[0].time) * speed
        self.beatmap = bmp


def graph_bpm(map_link, mods, link_type):
    map_obj = MapStats(map_link, mods, link_type)

    Log.log(f"Graphing BPM for {map_obj.title}")

    data = [(i.time / map_obj.speed_multiplier,
             1000 / i.ms_per_beat * 60 / map_obj.speed_multiplier)
            for i in map_obj.beatmap.timing_points if i.change]

    chart_points = list()
    for i, j in enumerate(data):
        if i != 0:
            last = data[i - 1]
            chart_points.append((j[0] - .01, last[1]))
        chart_points.append(j)
        if len(data) - 1 == i:
            chart_points.append((map_obj.beatmap.hitobjects[-1].time / map_obj.speed_multiplier, j[1]))

    points = pd.DataFrame(chart_points)
    points.columns = ["Time", "BPM"]

    col = (38 / 255, 50 / 255, 59 / 255, .9)
    sns.set(rc={'axes.facecolor': col,
                'text.color': (236 / 255, 239 / 255, 241 / 255),
                'figure.facecolor': col,
                'savefig.facecolor': col,
                'xtick.color': (176 / 255, 190 / 255, 197 / 255),
                'ytick.color': (176 / 255, 190 / 255, 197 / 255),
                'grid.color': (69 / 255, 90 / 255, 100 / 255),
                'axes.labelcolor': (240 / 255, 98 / 255, 150 / 255),
                'xtick.bottom': True,
                'xtick.direction': 'in',
                'figure.figsize': (6, 4),
                'savefig.dpi': 100
                })

    ax = sns.lineplot(x="Time", y="BPM", data=points, color=(240 / 255, 98 / 255, 150 / 255))

    length = int(map_obj.total_length) * 1000
    m = length / 50
    plt.xlim(-m, length + m)

    formatter = matplotlib.ticker.FuncFormatter(lambda ms, x: strftime('%M:%S', gmtime(ms // 1000)))
    ax.xaxis.set_major_formatter(formatter)

    comp = round(max(1, (map_obj.bpm_max - map_obj.bpm_min) / 20), 2)
    top = round(map_obj.bpm_max, 2) + comp
    bot = max(round(map_obj.bpm_min, 2) - comp, 0)
    dist = top - bot

    plt.yticks(np.arange(bot, top, dist / 6 - .0001))

    plt.ylim(bot, top)

    round_num = 0 if dist > 10 else 2

    formatter = matplotlib.ticker.FuncFormatter(lambda dig, y:
                                                f"{max(dig - .004, 0.0):.{round_num}f}")
    ax.yaxis.set_major_formatter(formatter)

    ax.xaxis.grid(False)
    width = 85
    map_text = "\n".join(wrap(f"{map_obj.title} by {map_obj.artist}", width=width)) + "\n" + \
               "\n".join(wrap(f"Mapset by {map_obj.creator}, "
                              f"Difficulty: {map_obj.version}", width=width))
    plt.title(map_text)

    plt.box(False)

    image = io.BytesIO()
    plt.savefig(image, bbox_inches='tight')
    image.seek(0)

    plt.clf()
    plt.close()
    return image


def get_map_link(link, **kwargs):
    if link.isnumeric():
        return int(link), "id"
    elif link.endswith(".osu"):
        return link, "url"
    elif "osu.ppy.sh" in link:
        if "#osu/" in link:
            return int(link.split("#osu/")[-1]), "id"
        elif "/b/" in link:
            return int(link.split("/b/")[-1]), "id"
        elif "/osu/" in link:
            return int(link.split("/osu/")[-1]), "id"
        elif "/beatmaps/" in link:
            return int(link.split("/beatmaps/")[-1]), "id"
        elif "/discussion/" in link:
            return int(link.split("/discussion/")[-1].split("/")[0]), "id"
    elif link.endswith(".osz"):
        return extract_map(link, **kwargs), "path"


def extract_map(mapset_id, diff=None):
    requests.get(f"https://bloodcat.com/osu/s/{mapset_id}")


def stat_play(play):
    map_obj = MapStats(play.beatmap_id, play.enabled_mods, "id")
    if play.rank.upper() == "F":
        completion = (play.count300 + play.count100 + play.count50 + play.countmiss) / map_obj.hit_objects
    else:
        completion = 1

    strain_bar = map_strain_graph(map_obj.beatmap, play.enabled_mods, completion)
    try:
        user_leaderboard = get_user_best(play.user_id)
        map_leaderboard = map_obj.leaderboard
        best_score = get_user_map_best(play.beatmap_id, play.user_id, play.enabled_mods)
        user = get_user(play.user_id)[0]
    except Exception as err:
        Log.error(err)
        return

    if best_score:
        best_score = best_score[0]

    recent = Dict({
        "user_id": play.user_id,
        "beatmap_id": play.beatmap_id,
        "rank": play.rank,
        "score": play.score,
        "combo": play.maxcombo,
        "count300": play.count300,
        "count100": play.count100,
        "count50": play.count50,
        "countmiss": play.countmiss,
        "mods": play.enabled_mods,
        "date": play.date,
        "unsubmitted": False,
        "pp": play.pp
    })

    recent.pb = 0
    recent.lb = 0
    replay = 0

    for j, i in enumerate(user_leaderboard):
        if compare_scores(i, play):
            recent.pb = j + 1
            break
    for j, i in enumerate(map_leaderboard):
        if compare_scores(i, play):
            recent.lb = j + 1
            break

    recent.username = user["username"]
    recent.user_rank = user["pp_rank"]
    recent.user_pp = user["pp_raw"]

    if best_score:
        if compare_scores(play, best_score):
            replay = best_score.replay_available
            recent.score_id = best_score.score_id
        else:
            recent.unsubmitted = True

    pp, _, _, _, acc = pytan.ppv2(
        aim_stars=map_obj.aim_stars,
        speed_stars=map_obj.speed_stars,
        base_ar=map_obj.ar,
        base_od=map_obj.od,
        n100=play.count100,
        n50=play.count50,
        nmiss=play.countmiss,
        mods=mod_int(play.enabled_mods),
        combo=play.maxcombo,
        ncircles=int(map_obj.count_normal * completion),
        nsliders=int(map_obj.count_spinner * completion),
        nobjects=int(map_obj.hit_objects * completion),
        max_combo=int(map_obj.max_combo * completion))

    pp_fc, _, _, _, acc_fc = pytan.ppv2(
        aim_stars=map_obj.aim_stars,
        speed_stars=map_obj.speed_stars,
        base_ar=map_obj.ar,
        base_od=map_obj.od,
        n100=play.count100,
        n50=play.count50,
        mods=mod_int(play.enabled_mods),
        ncircles=int(map_obj.count_normal * completion),
        nsliders=int(map_obj.count_spinner * completion),
        nobjects=int(map_obj.hit_objects * completion),
        max_combo=int(map_obj.max_combo * completion))

    recent.stars = map_obj.total
    recent.pp_fc = pp_fc
    recent.acc = acc
    recent.acc_fc = acc_fc

    if recent.pp is None:
        recent.pp = pp

    if replay:
        recent.ur = 0
        # TODO: make osr parser for unstable rate

    recent.completion = completion
    recent.strain_bar = strain_bar
    recent.map_obj = map_obj

    return recent


def compare_scores(a, b):
    if a.date != b.date:
        return False

    if a.user_id != b.user_id:
        return False

    return True


def map_strain_graph(map_obj, mods, progress=1., mode="", width=399., height=40., max_chunks=100, low_cut=30.):
    width = float(width)
    height = float(height)
    low_cut = float(low_cut)
    map_strains = get_strains(map_obj, mods, mode)
    strains, max_strain = map_strains["strains"], map_strains["max_strain"]

    strains_chunks = list()
    chunk_size = math.ceil(len(strains) / max_chunks)

    for i in range(0, len(strains), chunk_size):
        strain_part = strains[i:i + chunk_size]
        strains_chunks.append(max(strain_part))

    x = np.linspace(0, width, num=len(strains_chunks))
    y = np.minimum(low_cut,
                   height * 0.125 + height * .875 - np.array([i / max_strain for i in strains_chunks]) * height * .875)

    x = np.insert(x, 0, 0)
    x = np.insert(x, 0, 0)
    x = np.append(x, width)
    x = np.append(x, width)
    y = np.insert(y, 0, low_cut)
    y = np.insert(y, 0, low_cut)
    y = np.append(y, low_cut)
    y = np.append(y, low_cut)
    curves = list()
    curves.append(bezier.Curve(np.asfortranarray([[0.0, 0.0], [height, low_cut]]), degree=1))
    for i in range(1, len(y) - 1):
        node = np.asfortranarray([
            [avgpt(x, i - 1), x[i], avgpt(x, i)],
            [avgpt(y, i - 1), y[i], avgpt(y, i)]]
        )
        curves.append(
            bezier.Curve(node, degree=2)
        )
    curves.append(bezier.Curve(np.asfortranarray([[width, width], [low_cut, height]]), degree=1))
    curves.append(bezier.Curve(np.asfortranarray([[width, 0.0], [height, height]]), degree=1))
    polygon = bezier.CurvedPolygon(*curves)

    _, ax = plt.subplots(figsize=(round(width * 1.30), round(height * 1.30)), dpi=1)
    polygon.plot(pts_per_edge=200, color=(240 / 255, 98 / 255, 146 / 255, 1), ax=ax)
    plt.xlim(0, width)
    plt.ylim(height, 0)
    plt.axis('off')
    plt.box(False)

    image = io.BytesIO()
    fig1 = plt.gcf()
    fig1.savefig(image, bbox_inches='tight', transparent=True, pad_inches=0, dpi=1)
    image.seek(0)
    plt.clf()
    plt.close()

    img = Image.open(image)
    data = np.array(img)
    for j in data:
        for pos, i in enumerate(j):
            if pos > len(j) * progress:
                j[pos] = i / 1.5

            if i[3] != 0:
                j[pos][3] = i[3] / 159 * 255

    img = Image.fromarray(data)
    image.close()
    image = io.BytesIO()
    img.save(image, "png")
    image.seek(0)

    return image


def avgpt(points, index):
    return (points[index] + points[index + 1]) / 2


def get_strains(beatmap, mods, mode=""):
    stars = pytan.diff_calc().calc(beatmap, mod_int(mods))

    speed = speed_multiplier(mods)

    aim_strains = calculate_strains(1, beatmap.hitobjects, speed)
    speed_strains = calculate_strains(0, beatmap.hitobjects, speed)

    star_strains = list()
    max_strain = 0
    strain_step = OsuConsts.STRAIN_STEP.value * speed
    strain_offset = math.floor(beatmap.hitobjects[0].time / strain_step) * strain_step - strain_step
    max_strain_time = strain_offset

    for i in range(len(aim_strains)):
        star_strains.append(aim_strains[i] + speed_strains[i]
                            + abs(speed_strains[i] - aim_strains[i])
                            * OsuConsts.EXTREME_SCALING_FACTOR.value)

    chosen_strains = star_strains
    total = stars.total
    if mode == "aim":
        total = stars.aim
        chosen_strains = aim_strains
    if mode == "speed":
        total = stars.speed
        chosen_strains = speed_strains

    for i in chosen_strains:
        if i > max_strain:
            max_strain_time = i * OsuConsts.STRAIN_STEP.value + strain_offset
            max_strain = i

    return {
        "strains": chosen_strains,
        "max_strain": max_strain,
        "max_strain_time": max_strain_time,
        "max_strain_time_real": max_strain_time * speed,
        "total": total
    }


def calculate_strains(mode_type, hit_objects, speed_multiplier):
    strains = list()
    strain_step = OsuConsts.STRAIN_STEP.value * speed_multiplier
    interval_emd = math.ceil(hit_objects[0].time / strain_step) * strain_step
    max_strains = 0.0

    for i in range(len(hit_objects)):
        while hit_objects[i].time > interval_emd:
            strains.append(max_strains)
            if i > 0:
                decay = OsuConsts.DECAY_BASE.value[mode_type] ** \
                        (interval_emd - hit_objects[i - 1].time) / 1000
                max_strains = hit_objects[i - 1].strains[mode_type] * decay
            else:
                max_strains = 0.0
            interval_emd += strain_step
        max_strains = max(max_strains, hit_objects[i].strains[mode_type])

    strains.append(max_strains)
    for j, i in enumerate(strains):
        i *= 9.999
        strains[j] = math.sqrt(i) * OsuConsts.STAR_SCALING_FACTOR.value

    return strains


def embed_play(play_stats, client):
    desc = ""
    if play_stats.pb:
        desc = f"**__#{play_stats.pb} Top Play!__**"
    embed = discord.Embed(description=desc,
                          url=f"https://osu.ppy.sh/b/{play_stats.beatmap_id}",
                          title=f"{play_stats.map_obj.artist} – {play_stats.map_obj.title} [{play_stats.map_obj.version}]",
                          color=0xbb5577)

    embed.set_author(url=f"https://osu.ppy.sh/u/{play_stats.user_id}",
                     name=f"{play_stats.username} – {play_stats.user_pp:,}pp "
                          f"(#{play_stats.user_rank:,})",
                     icon_url=f"https://a.ppy.sh/{play_stats.user_id}?{int(time())}")

    embed.set_image(url="attachment://strains_bar.png")

    ranked_text = "Submitted"
    approved = play_stats.map_obj.approved
    if approved == 1:
        ranked_text = "Ranked"
    elif approved == 2:
        ranked_text = "Approved"
    elif approved == 3:
        ranked_text = "Qualified"
    elif approved == 4:
        ranked_text = "Loved"

    embed.set_footer(icon_url=f"https://a.ppy.sh/{play_stats.map_obj.creator_id}?{int(time())}",
                     text=f"Mapped by {play_stats.map_obj.creator} {separator} {ranked_text} on "
                          f"{play_stats.map_obj.approved_date.format('D MMMM YYYY')}")

    embed.set_thumbnail(url=f"https://b.ppy.sh/thumb/{play_stats.map_obj.beatmapset_id}l.jpg")

    play_results = f"{get_rank_emoji(play_stats.rank, client)} {separator} "
    if len(play_stats.mods) > 0:
        play_results += f"+{','.join(sanitize_mods(play_stats.mods))} {separator} "

    if play_stats.lb > 0:
        play_results += f"r#{play_stats.lb} {separator} "

    play_results += f"{play_stats.score:,} {separator} " \
                    f"{format_nums(play_stats.acc,2)}% {separator} " \
                    f"{play_stats.date.humanize()}"

    if play_stats.pp_fc > play_stats.pp:
        perfomacne = f"**{'*' if play_stats.unsubmitted else ''}{format_nums(play_stats.pp,2):,}" \
                     f"pp**{'*' if play_stats.unsubmitted else ''} ➔ {format_nums(play_stats.pp_fc,2):,}pp for " \
                     f"{format_nums(play_stats.acc_fc, 2)}% FC {separator} "
    else:
        perfomacne = f"**{format_nums(play_stats.pp,2):,}pp** {separator} "

    if play_stats.combo < play_stats.map_obj.max_combo:
        perfomacne += f"{play_stats.combo:,}/{play_stats.map_obj.max_combo:,}x"
    else:
        perfomacne += f"{play_stats.map_obj.max_combo:,}x"

    if play_stats.pp_fc > play_stats.pp:
        perfomacne += "\n"
    elif play_stats.ur or play_stats.count100 or play_stats.count50 or play_stats.countmiss:
        perfomacne += f" {separator} "

    if play_stats.count100 > 0:
        perfomacne += f"{play_stats.count100}x100"

    if play_stats.count50 > 0:
        if play_stats.count100 > 0:
            perfomacne += f" {separator} "
        perfomacne += f"{play_stats.count50}x50"

    if play_stats.countmiss > 0:
        if play_stats.count100 > 0 or play_stats.count50 > 0:
            perfomacne += f" {separator} "
        perfomacne += f"{play_stats.countmiss}xMiss"

    if play_stats.ur is not None and play_stats.ur > 0:
        pass
        # TODO: implrmrnt UR and CV

    if play_stats.completion < 1:
        perfomacne += f"\n**{format_nums(play_stats.completion * 100, 2)}%** completion"

    embed.add_field(name=play_results, value=perfomacne)

    beatmap_info = f"{arrow.Arrow(2019, 1, 1).shift(seconds=play_stats.map_obj.total_length).format('mm:ss')} ~ " \
                   f"CS**{format_nums(play_stats.map_obj.cs, 1)}** " \
                   f"AR**{format_nums(play_stats.map_obj.ar, 1)}** " \
                   f"OD**{format_nums(play_stats.map_obj.od, 1)}** " \
                   f"HP**{format_nums(play_stats.map_obj.hp, 1)}** ~ "

    if play_stats.map_obj.bpm_min != play_stats.map_obj.bpm_max:
        beatmap_info += f"{format_nums(play_stats.map_obj.bpm_min,1)}-{format_nums(play_stats.map_obj.bpm_max,1)} " \
                        f"(**{format_nums(play_stats.map_obj.bpm,1)}**) "
    else:
        beatmap_info += f"**{format_nums(play_stats.map_obj.bpm,1)}** "

    beatmap_info += f"BPM ~ " \
                    f"**{format_nums(play_stats.stars,2)}**★"

    embed.add_field(name="Beatmap Information", value=beatmap_info)

    return embed
