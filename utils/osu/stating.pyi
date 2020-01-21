from io import BytesIO
from typing import Union, List, Optional, TypedDict, Dict

import arrow
import oppadc

from .utils import parse_mods_int, calculate_acc, speed_multiplier


class Play:
    def __init__(self, play_dict: dict = ...): ...

    score: int = ...
    maxcombo: int = ...
    countmiss: int = ...
    count50: int = ...
    count100: int = ...
    count300: int = ...
    perfect: bool = ...
    enabled_mods: parse_mods_int = ...
    user_id: int = ...
    date: arrow.Arrow = ...
    rank: str = ...
    accuracy: calculate_acc = ...
    beatmap_id: int = ...
    replay_available: bool = ...
    score_id: int = ...
    performance_points: float = ...

    def __eq__(self, other: Play = ...) -> bool: ...


class MapStats:
    def __init__(self, map_id: Union[str, int] = ..., mods: list = ..., link_type: str = ...): ...

    speed_multiplier: speed_multiplier
    artist: str
    title: str
    artist_unicode: str
    title_unicode: str
    version: str
    bpm_min: float
    bpm_max: float
    total_length: float
    max_combo: int
    creator: str
    creator_id: int
    map_creator: dict  # todo
    base_cs: float
    base_ar: float
    base_od: float
    base_hp: float
    cs: float
    ar: float
    od: float
    hp: float
    mode: int
    hit_objects: int
    count_normal: int
    count_slider: int
    count_spinner: int
    approved: Optional[int]
    submit_date: Optional[arrow.Arrow]
    approved_date: Optional[arrow.Arrow]
    last_update: Optional[arrow.Arrow]
    beatmap_id: Optional[int]
    beatmapset_id: Optional[int]
    source: Optional[str]
    genre_id: Optional[int]
    language_id: Optional[int]
    file_md5: Optional[str]
    tags: Optional[str]
    favourite_count: Optional[int]
    rating: Optional[float]
    playcount: Optional[int]
    passcount: Optional[int]
    download_unavailable: Optional[bool]
    audio_unavailable: Optional[bool]
    leaderboard: List[Optional[Play]]
    aim_stars: float
    speed_stars: float
    total: float
    bpm: float
    beatmap: oppadc.OsuMap


class _StatPlayTypes(TypedDict):
    user_id: int
    beatmap_id: int
    rank: str
    score: int
    combo: int
    count300: int
    count100: int
    count50: int
    countmiss: int
    mods: list
    date: arrow.Arrow
    unsubmitted: bool
    performance_points: float
    pb: int
    lb: int
    username: str
    user_rank: int
    user_pp: int
    stars: float
    pp_fc: float
    acc: float
    acc_fc: float
    replay: Optional[str]
    completion: float
    strain_bar: BytesIO
    map_obj: MapStats
    score_id: Optional[int]
    ur: Optional[float]


def stat_play(play: Play = ...) -> _StatPlayTypes: ...


def calculate_strains(mode_type: int = ..., hit_objects: list = ..., speed_multiplier: float = ...) -> List[float]: ...


def get_strains(beatmap: oppadc.OsuMap = ..., mods: Union[list, set] = ..., mode: str = ...) -> \
        Dict[List[float], float, float, float, float]: ...
