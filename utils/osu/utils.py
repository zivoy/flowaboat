import io
import math
import os
import zipfile
from typing import Union, Tuple

import discord
import regex
import requests

from ..config import Config
from ..discord import fetch_emote
from ..errors import NoBeatmap
from ..osu import OsuConsts, MODS_RE
from ..utils import Log


def parse_mods_string(mods: str) -> list:
    """
    turns mod str into mod list

    :param mods: mod string
    :return: mod list
    """
    if mods == '' or mods == "nomod":
        return []
    mods = mods.replace("+", "").upper()
    mods_included = MODS_RE.match(mods)
    if mods_included is None:
        Log.error(f"Mods not valid: {mods}")
        return []  # None
    matches = mods_included.captures(1)
    return list(set(matches))


def parse_mods_int(mods: int) -> list:
    """
    turns bitwise flag into mod list

    :param mods: mod int
    :return: mod list
    """
    if not mods:
        return []
    mod_list = list()
    for i in OsuConsts.MODS_INT.value:
        if i & mods:
            mod_list.append(OsuConsts.MODS_INT.value[i])
    return mod_list


def sanitize_mods(mods: Union[list, set]) -> Union[list, set]:
    """
    gets rid of mods that have similar effects

    :param mods: mod list
    :return: fixed mod list
    """
    if "NC" in mods and "DT" in mods:
        mods.remove("DT")
    if "PF" in mods and "SD" in mods:
        mods.remove("SD")
    return mods


def mod_int(mod_list: Union[list, set, int]) -> int:
    """
    cleans and turns the list of mods into bitwise integer

    :param mod_list: list of mods
    :return: bitwise flag
    """
    if isinstance(mod_list, int):
        return mod_list
    if isinstance(mod_list, str):
        mod_list = parse_mods_string(mod_list)
    else:
        mod_list = set(mod_list)
    if "NC" in mod_list:
        mod_list.add("DT")

    mod_list = filter(lambda x: x in OsuConsts.DIFF_MODS.value, mod_list)

    res = 0

    for i in mod_list:
        res += OsuConsts.MODS.value[i]
    return res


def get_map_link(link: str, **kwargs) -> Tuple[Union[int, str], str]:
    """
    gets link type and corresponding value

    :param link: a link or id
    :param kwargs: for the case that its a osz file
    :return: id or other identifier and str of type
    """
    if link.isnumeric():
        return int(link), "id"
    if link.endswith(".osu"):
        return link, "url"
    if "osu.ppy.sh" in link:
        if "#osu/" in link:
            return int(link.split("#osu/")[-1]), "id"
        if "/b/" in link:
            return int(link.split("/b/")[-1]), "id"
        if "/osu/" in link:
            return int(link.split("/osu/")[-1]), "id"
        if "/beatmaps/" in link:
            return int(link.split("/beatmaps/")[-1]), "id"
        if "/discussion/" in link:
            return int(link.split("/discussion/")[-1].split("/")[0]), "id"
    if link.endswith(".osz"):
        return download_mapset(link, **kwargs), "path"


def calculate_acc(n300: int, n100: int, n50: int, nMiss: int) -> float:
    """
    calculate the acc based on number of hits

    :param n300: number of 300s
    :param n100: number of 100s
    :param n50: number of 50s
    :param nMiss: number of misses
    :return: accuracy
    """
    return (50 * n50 + 100 * n100 + 300 * n300) / (300 * (nMiss + n50 + n100 + n300))


def speed_multiplier(mods: Union[list, set]) -> float:
    """
    gets the speed multiplier based on mods applied

    :param mods: list of mods
    :return: speed multiplier
    """
    speed = 1.
    if "DT" in mods or "NC" in mods:
        speed *= OsuConsts.DT_SPD.value
    elif "HT" in mods:
        speed *= OsuConsts.HT_SPD.value
    return speed


def get_rank_emoji(rank: str, client: discord.Client) -> Union[bool, discord.Emoji, str]:
    """
    gets the rank emoji

    :param rank: rank to fetch
    :param client: discord client
    :return: emoji or name
    """
    if rank == "XH":
        emote = fetch_emote("XH_Rank", None, client)
        return emote if emote else "Silver SS"
    if rank == "X":
        emote = fetch_emote("X_Rank", None, client)
        return emote if emote else "SS"
    if rank == "SH":
        emote = fetch_emote("SH_Rank", None, client)
        return emote if emote else "Silver S"
    if rank == "S":
        emote = fetch_emote("S_Rank", None, client)
        return emote if emote else "S"
    if rank == "A":
        emote = fetch_emote("A_Rank", None, client)
        return emote if emote else "A"
    if rank == "B":
        emote = fetch_emote("B_Rank", None, client)
        return emote if emote else "B"
    if rank == "C":
        emote = fetch_emote("C_Rank", None, client)
        return emote if emote else "C"
    if rank == "D":
        emote = fetch_emote("D_Rank", None, client)
        return emote if emote else "D"
    if rank == "F":
        emote = fetch_emote("F_Rank", None, client)
        return emote if emote else "Fail"
    return False


class CalculateMods:
    def __init__(self, mods: Union[list, str]):
        """
        calculates the modifications that happens to values when you apply mods

        :param mods: mods to apply
        """
        self.mods = mods
        if list(mods) != mods:
            self.mods: list = parse_mods_string(mods)

        #     Log.log(mods.replace("+", ""))
        # Log.log(self.mods)

    def ar(self, raw_ar: Union[float, int]) -> Tuple[float, float, list]:
        """
        calculates approach rate with mods allied to it

        :param raw_ar: input ar
        :return: outputs new ar and how long you have to react as well as mods applied
        """
        ar_multiplier = 1.

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

    def cs(self, raw_cs: Union[float, int]) -> Tuple[float, list]:
        """
        calculate the circle size with mod applied to it

        :param raw_cs: input cs
        :return: outputs new cs and mods applied to it
        """
        cs_multiplier = 1.

        if "HR" in self.mods:
            cs_multiplier *= OsuConsts.HR_CS.value
        elif "EZ" in self.mods:
            cs_multiplier *= OsuConsts.EZ_CS.value

        cs = min(raw_cs * cs_multiplier, 10)

        return cs, self.mods

    def od(self, raw_od: Union[float, int]) -> Tuple[float, float, list]:
        """
        calculates the overall difficulty with mods allied to it

        :param raw_od: input od
        :return: new od, how long you have to react in ms and mod allied
        """
        od_multiplier = 1.
        speed = 1.

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

    def hp(self, raw_hp: Union[float, int]) -> Tuple[float, list]:
        """
        calculates the hp with the mods applied

        :param raw_hp: input hp
        :return: outputs hp and mods applied to it
        """
        hp_multiplier = 1.

        if "HR" in self.mods:
            hp_multiplier *= OsuConsts.HR_HP.value
        elif "EZ" in self.mods:
            hp_multiplier *= OsuConsts.EZ_HP.value

        hp = min(raw_hp * hp_multiplier, 10)

        return hp, self.mods


def download_mapset(link_id: Union[str, int] = None, link: str = None) -> str:
    """
    downloads an osu mapset

    :param link_id: a map id
    :param link: a direct link to osz file
    :return: the path to downloaded folder
    """
    if link_id is None and link is None:
        raise NoBeatmap("No beatmap provided")
    if link_id is not None:
        link = f"https://bloodcat.com/osu/s/{link_id}"
        name = str(link_id)
    else:
        name = link.split('/')[-1].split(".osz")[0]

    mapset = requests.get(link)
    headers = mapset.headers.get('content-type').lower()

    if link_id is not None and "octet-stream" not in headers:
        link = f"https://osu.gatari.pw/d/{link_id}"
        mapset = requests.get(link)
        headers = mapset.headers.get('content-type').lower()
        if "octet-stream" not in headers:
            Log.error("Could not find beatmap:", link_id)
            raise NoBeatmap("Could not find beatmap")

    location = os.path.join(Config.osu_cache_path, name)

    map_files = zipfile.ZipFile(io.BytesIO(mapset.content), "r")

    osu_file = regex.compile(r".+\[(\D+)\]\.osu")

    for i in map_files.infolist():
        for j in [".osu", ".jpg", ".jpeg", ".png", ".mp3"]:
            if i.filename.endswith(j):
                if j == ".osu":
                    diff_name = osu_file.match(i.filename).captures(1)[0]
                    i.filename = f"{diff_name}.osu"
                map_files.extract(i, location)
                break

    return location
