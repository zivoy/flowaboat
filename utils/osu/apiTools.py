from typing import Union, List

import arrow

from utils import DATE_FORM
from .play_object import Play
from ..config import Config
from ..errors import UserNonexistent, NoReplay, NoLeaderBoard, NoPlays
from ..osu import OSU_API
from ..utils import Log, dict_string_to_nums


def get_user(user: Union[int, str]) -> dict:
    """
    gets users profile information

    :param user: username
    :return: dictionary containing the information
    """
    response = OSU_API.get('/get_user', {"u": user})
    response = response.json()

    if Config.debug:
        Log.log(response)

    if not response:
        raise UserNonexistent(f"Couldn't find user: {user}")

    for i, _ in enumerate(response):
        response[i]["join_date"] = arrow.get(response[i]["join_date"], DATE_FORM)
        dict_string_to_nums(response[i])

    return response


def get_leaderboard(beatmap_id: Union[str, int], limit: int = 100) -> List[Play]:
    """
    gets leader board for beatmap

    :param beatmap_id: beatmap id
    :param limit: number of items to get
    :return: list of plays
    """
    response = OSU_API.get('/get_scores', {"b": beatmap_id, "limit": limit}).json()

    if Config.debug:
        Log.log(response)

    if not response:
        raise NoLeaderBoard("Couldn't find leader board for this beatmap")

    for i, _ in enumerate(response):
        response[i]["beatmap_id"] = beatmap_id
        response[i] = Play(response[i])

    return response


def get_user_map_best(beatmap_id: Union[int, str], user: Union[int, str],
                      enabled_mods: int = 0) -> List[Play]:
    """
    gets users best play on map

    :param beatmap_id: beatmap id
    :param user: username
    :param enabled_mods: mods used
    :return: list of plays
    """
    response = OSU_API.get('/get_scores', {"b": beatmap_id, "u": user, "mods": enabled_mods}).json()

    if Config.debug:
        Log.log(response)

    # if len(response) == 0:
    #     raise NoScore("Couldn't find user score for this beatmap")

    for i, j in enumerate(response):
        response[i] = Play(j)
        response[i].beatmap_id = beatmap_id

    return response


def get_user_best(user: Union[int, str], limit: int = 100) -> List[Play]:
    """
    gets users best plays

    :param user: username
    :param limit: number of items to fetch
    :return: list of plays
    """
    response = OSU_API.get('/get_user_best', {"u": user, "limit": limit})
    response = response.json()

    if Config.debug:
        Log.log(response)

    if not response:
        raise NoPlays(f"No top plays found for {user}")

    for i, j in enumerate(response):
        response[i] = Play(j)

    return response


def get_user_recent(user: Union[int, str], limit: int = 10) -> List[Play]:
    """
    gets user most recent play by index

    :param user: user name
    :param limit: number of items to fetch
    :return: list of plays
    """
    response = OSU_API.get('/get_user_recent', {"u": user, "limit": limit}).json()

    if Config.debug:
        Log.log(response)

    if not response:
        raise NoPlays(f"No recent plays found for {user}")

    for i, j in enumerate(response):
        response[i] = Play(j)

    return response


def get_replay(beatmap_id: Union[int, str], user_id: Union[int, str],
               mods: int, mode: int = 0) -> str:
    """
    gets the replay string of play

    :param beatmap_id: beatmap id
    :param user_id: username
    :param mods: mods used on play
    :param mode: mode played on
    :return: base64 encoded replay string
    """
    response = OSU_API.get("/get_replay", {"b": beatmap_id, "u": user_id,
                                           "mods": mods, "m": mode}).json()

    if "error" in response:
        raise NoReplay("Could not find replay for this user")

    replay = response["content"]

    return replay


def get_top(user: str, index: int, rb: bool = False, ob: bool = False) -> Play:
    """
    gets user top play

    :param user: username
    :param index: index to get
    :param rb: sort by recent best
    :param ob: sort by old best
    :return: Play object
    """
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


def get_recent(user: str, index: int) -> Play:
    """
    gets the users recent play by index

    :param user: username of player
    :param index: index to fetch
    :return: Play object
    """
    index = min(max(index, 1), 50)
    response = get_user_recent(user, index)

    if len(response) < index:
        index = len(response)

    recent_raw = response[index - 1]

    return recent_raw
