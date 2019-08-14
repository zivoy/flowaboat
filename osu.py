from enum import Enum
from utils import *

import warnings
from arrow.factory import ArrowParseWarning

warnings.simplefilter("ignore", ArrowParseWarning)

osu_api = Api("https://osu.ppy.sh/api", {"k": Config.credentials.osu_api_key})


class OsuConsts(Enum):
    # "": 0,
    MODS = {
        "NF": 2**0,
        "EZ": 2**1,
        "TD": 2**2,
        "HD": 2**3,
        "HR": 2**4,
        "SD": 2**5,
        "DT": 2**6,
        "RX": 2**7,
        "HT": 2**8,
        "NC": 2**9,
        "FL": 2**10,
        "AT": 2**11,
        "SO": 2**12,
        "AP": 2**13,
        "PF": 2**14,
        "4K": 2**15,
        "5K": 2**16,
        "6K": 2**17,
        "7K": 2**18,
        "8K": 2**19,
        "FI": 2**20,
        "RD": 2**21,
        "LM": 2**22,
        "TR": 2**23,
        "9K": 2**24,
        "10K": 2**25,
        "1K": 2**26,
        "3K": 2**27,
        "2K": 2**28,
        "V2": 2**29
    }

    R_MODS = {v: k for k, v in MODS.items()}

    DIFF_MODS = ["HR", "EZ", "DT", "HT"]
    TIME_MODS = ["DT", "HT"]

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


mods_re = regex.compile(rf"^({'|'.join(OsuConsts.MODS.value.keys())})+$")


def parse_mods_string(mods):
    if mods == '':
        return []
    mods = mods.replace("+", "").upper()
    mods_included = mods_re.match(mods)
    if mods_included is None:
        Log.error(f"Mods not valid: {mods}")
        return []  # None
    matches = mods_included.captures(1)
    return list(set(matches))


def parse_mods(mod_int):
    mod_bin = bin(mod_int)[2:][::-1]
    mods = list()
    for i in range(len(mod_bin)):
        if mod_bin[i] == '1':
            mods.append(OsuConsts.R_MODS.value[1 << i])
    return mods


class CalculateMods:
    def __init__(self, mods):
        self.mods = parse_mods_string(mods)

        Log.log(mods.replace("+", ""))
        Log.log(self.mods)

    def ar(self, raw_ar):
        speed = 1
        ar_multiplier = 1

        if "DT" in self.mods:
            speed *= OsuConsts.DT_SPD.value
        elif "HT" in self.mods:
            speed *= OsuConsts.HT_SPD.value

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

        odms = OsuConsts.OD0_MS.value - math.cos(OsuConsts.OD_MS_STEP.value * od)
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


def get_user(user):
    response = osu_api.get('/get_user', {"u": user})
    response = response.json()

    Log.log(response)

    if len(response) == 0:
        return False, "Couldn't find user"

    return True, response


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


def get_top(user, index, rb=None, ob=None):
    index = min(max(index, 1), 100)
    limit = 100 if rb or ob else index
    response = osu_api.get('/get_user_best', {"u": user, "limit": limit})
    response = response.json()

    Log.log(response)

    if len(response) == 0:
        return False, f"No top plays found for {user}"

    for i in range(len(response)):
        response[i]["date"] = arrow.get(response[i]["date"], date_form)

    if rb:
        response = sorted(response, key=lambda k: k["date"], reverse=True)
    if ob:
        response = sorted(response, key=lambda k: k["date"])

    if len(response) < index:
        index = len(response)

    recent_raw = response[index-1]

    return True, recent_raw
