from enum import Enum
import regex
from utils import *


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


def parse_mods(mods):
    if mods == '':
        return []
    mods = mods.replace("+", "").upper()
    r = regex.compile(rf"^({'|'.join(OsuConsts.MODS.value.keys())})+$")
    x = r.match(mods)
    if x is None:
        Log.error(f"Mods not valid: {mods}")
        return []  # None
    matches = x.captures(1)
    return list(set(matches))


def calculate_ar(raw_ar, mods):
    mod_list = parse_mods(mods)

    Log.log(mods.replace("+", ""))
    Log.log(mod_list)

    speed = 1
    ar_multiplier = 1

    if "DT" in mod_list:
        speed *= OsuConsts.DT_SPD.value
    elif "HT" in mod_list:
        speed *= OsuConsts.HT_SPD.value

    if "HR" in mod_list:
        ar_multiplier *= OsuConsts.HR_AR.value
    elif "EZ" in mod_list:
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

    return ar, ar_ms, mod_list
