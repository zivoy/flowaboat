from enum import Enum

import regex

from ..config import Config
from ..utils import Api


class OsuConsts(Enum):
    """
    all constants related to osu
    """
    # "": 0,
    MODS = {
        "NF": 1 << 0,
        "EZ": 1 << 1,
        "TD": 1 << 2,
        "HD": 1 << 3,
        "HR": 1 << 4,
        "SD": 1 << 5,
        "DT": 1 << 6,
        "RX": 1 << 7,
        "HT": 1 << 8,
        "NC": 1 << 9,
        "FL": 1 << 10,
        "AT": 1 << 11,
        "SO": 1 << 12,
        "AP": 1 << 13,
        "PF": 1 << 14,
        "4K": 1 << 15,
        "5K": 1 << 16,
        "6K": 1 << 17,
        "7K": 1 << 18,
        "8K": 1 << 19,
        "FI": 1 << 20,
        "RD": 1 << 21,
        "LM": 1 << 22,
        "TR": 1 << 23,
        "9K": 1 << 24,
        "10K": 1 << 25,
        "1K": 1 << 26,
        "3K": 1 << 27,
        "2K": 1 << 28,
        "V2": 1 << 29
    }

    MODS_INT = {v: k for k, v in MODS.items()}

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


MODS_RE = regex.compile(rf"^({'|'.join(OsuConsts.MODS.value.keys())})+$")

OSU_API = Api("https://osu.ppy.sh/api", 60, {"k": Config.credentials.osu_api_key})
# todo make a list of apis for multi server comparability


__all__ = ["OsuConsts", "MODS_RE", "OSU_API", "utils", "apiTools", "stating", "graphing", "embedding"]
