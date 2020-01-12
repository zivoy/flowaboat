from typing import Union, List

from .play_object import Play


def get_user(user: Union[int, str] = ...) -> dict: ...


def get_leaderboard(beatmap_id: Union[str, int] = ..., limit: int = ...) -> List[Play]: ...


def get_user_map_best(beatmap_id: Union[int, str] = ..., user: Union[int, str] = ...,
                      enabled_mods: int = ...) -> List[Play]: ...


def get_user_best(user: Union[int, str] = ..., limit: int = ...) -> List[Play]: ...


def get_user_recent(user: Union[int, str] = ..., limit: int = ...) -> List[Play]: ...


def get_replay(beatmap_id: Union[int, str] = ..., user_id: Union[int, str] = ...,
               mods: int = ..., mode: int = ...) -> str: ...


def get_top(user: str = ..., index: int = ..., rb: bool = ..., ob: bool = ...) -> Play: ...


def get_recent(user: str = ..., index: int = ...) -> Play: ...
