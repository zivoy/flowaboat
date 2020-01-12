from typing import Dict, List

import regex

from ..utils import Api


class OsuConsts:
    MODS = Dict[int]
    MODS_INT = Dict[int]
    DIFF_MODS = List[str]
    TIME_MODS = List[str]
    AR_MS_STEP1: float
    AR_MS_STEP2: float
    AR0_MS: float
    AR5_MS: float
    AR10_MS: float
    OD_MS_STEP: float
    OD0_MS: float
    OD10_MS: float
    DT_SPD: float
    HT_SPD: float
    HR_AR: float
    EZ_AR: float
    HR_CS: float
    EZ_CS: float
    HR_OD: float
    EZ_OD: float
    HR_HP: float
    EZ_HP: float
    STRAIN_STEP: float
    DECAY_BASE: List[float]
    STAR_SCALING_FACTOR: float
    EXTREME_SCALING_FACTOR: float
    DECAY_WEIGHT: float


MODS_RE: regex.Regex
OSU_API: Api  # List[Api]
