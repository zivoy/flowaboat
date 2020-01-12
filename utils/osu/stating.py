import math

import arrow
import oppadc as oppa
import requests

from utils import DATE_FORM
from .apiTools import get_leaderboard, get_user, get_user_map_best, get_user_best, get_replay
from .graphing import map_strain_graph
from .utils import speed_multiplier, mod_int, CalculateMods
from ..errors import BadMapFile, BadLink, NoLeaderBoard, BadId
from ..osu import OSU_API, OsuConsts
from ..utils import dict_string_to_nums, Dict, Log


class MapStats:
    def __init__(self, map_id, mods, link_type="id"):
        """
        get stats on map // map api

        :param map_id:
        :param mods: mod
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

        bmp = oppa.OsuMap(raw_str=raw_map)  # , auto_parse=True)

        if not bmp.hitobjects:
            raise BadMapFile

        speed = speed_multiplier(mods)

        map_creator = get_user(bmp.creator)[0]
        stats = bmp.getStats(mod_int(mods))
        diff = CalculateMods(mods)

        length = bmp.hitobjects[-1].starttime
        change_list = [i for i in bmp.timingpoints if i.change]
        bpm_avg = list()
        bpm_list = list()
        for j, i in enumerate(change_list):
            if i.change:
                if j + 1 == len(change_list):
                    dur = length - i.starttime
                else:
                    dur = change_list[j + 1].starttime - i.starttime
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
        self.total_length = (length - bmp.hitobjects[0].starttime) / 1000. / speed
        self.max_combo = 0
        self.creator = bmp.creator
        self.creator_id = map_creator["user_id"]
        self.map_creator = Dict(map_creator)  # todo make user object
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
        self.count_normal = bmp.amount_circle
        self.count_slider = bmp.amount_slider
        self.count_spinner = bmp.amount_spinner
        bmp.getStats()

        if link_type == "id":
            self.approved = 0
            self.submit_date = None
            self.approved_date = None
            self.last_update = None
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
            self.download_unavailable = False
            self.audio_unavailable = False

            mods_applied = mod_int(mods)
            map_web = OSU_API.get("/get_beatmaps", {"b": map_id, "mods": mods_applied}).json()
            if not map_web:
                raise BadId
            dict_string_to_nums(map_web[0])
            for i, j in map_web[0].items():
                setattr(self, i, j)
            self.submit_date = arrow.get(self.submit_date, DATE_FORM)
            self.approved_date = arrow.get(self.approved_date, DATE_FORM)
            self.last_update = arrow.get(self.last_update, DATE_FORM)
            self.download_unavailable = bool(self.download_unavailable)
            self.audio_unavailable = bool(self.audio_unavailable)

        try:
            self.leaderboard = get_leaderboard(map_id)
        except NoLeaderBoard:
            self.leaderboard = []

        if self.max_combo is None:
            self.max_combo = bmp.maxCombo()
        self.aim_stars = stats.aim  # not sure if its aim or aim_difficulty
        self.speed_stars = stats.speed
        self.total = stats.total
        self.bpm = sum(bpm_avg) / (length - bmp.hitobjects[0].starttime) * speed
        self.beatmap = bmp


def stat_play(play):
    """
    gets statistics on osu play and graph on play

    :param play: a users play
    :return: a dict with information on play keys -> [user_id,
                                                        beatmap_id,
                                                        rank,
                                                        score,
                                                        combo,
                                                        count300,
                                                        count100,
                                                        count50,
                                                        countmiss,
                                                        mods,
                                                        date,
                                                        unsubmitted,
                                                        performance_points,
                                                        pb,
                                                        lb,
                                                        username,
                                                        user_rank,
                                                        user_pp,
                                                        stars,
                                                        pp_fc,
                                                        acc,
                                                        acc_fc,
                                                        replay,
                                                        completion,
                                                        strain_bar,
                                                        map_obj,
                                                        {score_id,
                                                        ur}]
    """
    map_obj = MapStats(play.beatmap_id, play.enabled_mods, "id")
    if play.rank.upper() == "F":
        completion = (play.count300 + play.count100 + play.count50 + play.countmiss) \
                     / map_obj.hit_objects
    else:
        completion = 1

    strain_bar = map_strain_graph(get_strains(map_obj.beatmap, play.enabled_mods, ""), completion)
    try:
        user_leaderboard = get_user_best(play.user_id)
        map_leaderboard = map_obj.leaderboard
        best_score = get_user_map_best(play.beatmap_id, play.user_id, mod_int(play.enabled_mods))
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
        "performance_points": play.performance_points
    })

    recent.pb = 0
    recent.lb = 0
    replay = 0

    for j, i in enumerate(user_leaderboard):
        if i == play:
            recent.pb = j + 1
            break
    for j, i in enumerate(map_leaderboard):
        if i == play:
            recent.lb = j + 1
            break

    recent.username = user["username"]
    recent.user_rank = user["pp_rank"]
    recent.user_pp = user["pp_raw"]

    if best_score:
        if play == best_score:
            replay = best_score.replay_available
            recent.score_id = best_score.score_id
        else:
            recent.unsubmitted = True

    pp = map_obj.beatmap.getPP(Mods=mod_int(play.enabled_mods), recalculate=True,
                               combo=play.maxcombo, misses=play.countmiss,
                               n300=play.count300, n100=play.count100, n50=play.count50)
    pp_fc = map_obj.beatmap.getPP(Mods=mod_int(play.enabled_mods), n100=play.count100,
                                  n50=play.count50, n300=play.count300 + play.countmiss,
                                  recalculate=True)

    recent.stars = map_obj.total
    recent.pp_fc = pp_fc.total_pp
    recent.acc = pp.accuracy
    recent.acc_fc = pp_fc.accuracy

    if recent.performance_points is None:
        recent.performance_points = pp.total_pp

    recent.replay = None
    if replay:
        recent.replay = get_replay(play.beatmap_id, play.user_id, mod_int(play.enabled_mods), 0)

        recent.ur = 0
        # TODO: make osr parser for unstable rate

    recent.completion = completion
    recent.strain_bar = strain_bar
    recent.map_obj = map_obj

    return recent


def calculate_strains(mode_type, hit_objects, speed_multiplier):
    """
    get strains of map at all times

    :param mode_type: mode type [speed, aim]
    :param hit_objects: list of hitobjects
    :param speed_multiplier: the speed multiplier induced by mods
    :return: list of strains
    """
    strains = list()
    strain_step = OsuConsts.STRAIN_STEP.value * speed_multiplier
    interval_emd = math.ceil(hit_objects[0].starttime / strain_step) * strain_step
    max_strains = 0.0

    for i, _ in enumerate(hit_objects):
        while hit_objects[i].starttime > interval_emd:
            strains.append(max_strains)
            if i > 0:
                decay = OsuConsts.DECAY_BASE.value[mode_type] ** \
                        (interval_emd - hit_objects[i - 1].starttime) / 1000
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


def get_strains(beatmap, mods, mode=""):
    """
    get all stains in map

    :param beatmap: beatmap object
    :param mods: mods used
    :param mode: [aim|speed] for type of strains to get
    :return: dict of strains keys -> [strains, max_strain, max_strain_time,
                                    max_strain_time_real, total]
    """
    stars = beatmap.getStats(mod_int(mods))

    speed = speed_multiplier(mods)

    aim_strains = calculate_strains(1, beatmap.hitobjects, speed)
    speed_strains = calculate_strains(0, beatmap.hitobjects, speed)

    star_strains = list()
    max_strain = 0.
    strain_step = OsuConsts.STRAIN_STEP.value * speed
    strain_offset = math.floor(beatmap.hitobjects[0].starttime / strain_step) \
                    * strain_step - strain_step
    max_strain_time = strain_offset

    for i, _ in enumerate(aim_strains):
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
