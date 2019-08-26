"""
Module for processing and handling replays
"""
import lzma
from base64 import b64decode, b64encode
from io import StringIO

import bezier
import numpy as np
import pandas as pd
import requests


def lzma_replay_to_df(lzma_byte_string):
    """
    Turn a lzma stream into a pandas dataframe of the replay
    :param lzma_byte_string: lzma encoded byte string
    :return: pandas dataframe. columns are "offset", "x pos", "y pos", "clicks"
    """
    stream = lzma.decompress(lzma_byte_string)
    dataframe = info_string_to_df(stream)
    dataframe.columns = ["ms since last", "x pos", "y pos", "clicks"]
    seed = 0

    if dataframe["ms since last"].iloc[-1] == -12345:
        seed = int(dataframe["clicks"].iloc[-1])
        dataframe.drop(dataframe.tail(1).index, inplace=True)
    smallidx = dataframe["ms since last"].idxmin()
    offset = 0
    if dataframe["ms since last"].iloc[smallidx] < 0:
        offset = int(dataframe.head(smallidx).sum()["ms since last"])
        dataframe.drop(dataframe.head(smallidx).index, inplace=True)
    dataframe["ms since last"] = dataframe["ms since last"].replace(0, 1)

    dataframe['offset'] = dataframe["ms since last"].cumsum() + offset
    dataframe = dataframe.drop(columns=["ms since last"])
    return dataframe, seed


def info_string_to_df(info):
    """
    Split a string separated into sections by , and into items by | into pandas dataframe
    :param info: byte string
    :return: pandas dataframe
    """
    dataframe = pd.read_csv(StringIO(str(info)[2:-1]), sep="|", lineterminator=',', header=None)
    return dataframe


def replay_string_to_df(replay):
    """
    Decodes a base 64 encoded replay string into a pandas dataframe
    :param replay: base 64 encode byte string
    :return: pandas dataframe. columns are "offset", "x pos", "y pos", "clicks"

    """
    byte_string = b64decode(replay)
    dataframe, _ = lzma_replay_to_df(byte_string)
    return dataframe


def open_file(file_name):
    """
    Opens a replay file and returns info on replay
    :param file_name: file name including path
    :return: ParseReplayByteSting object
    """
    with open(file_name, "rb") as replay:
        return ParseReplayByteSting(replay.read())


def open_link(link):
    """
    Opens a replay file from link and returns info on replay
    :param link: link to replay
    :return: ParseReplayByteSting object
    """
    replay = requests.get(link)
    return ParseReplayByteSting(replay.content)


class ParseReplayByteSting:
    """
    Contains info from replay file
    :param byte_string: byte string containing replay info
    """

    def __init__(self, byte_string):
        byte_string, self.gamemode = get_byte(byte_string)
        byte_string, self.game_version = get_integer(byte_string)
        byte_string, self.map_md5_hash = get_string(byte_string)
        byte_string, self.player_name = get_string(byte_string)
        byte_string, self.replay_md5_hash = get_string(byte_string)

        byte_string, self.count300 = get_short(byte_string)
        byte_string, self.count100 = get_short(byte_string)
        byte_string, self.count50 = get_short(byte_string)
        byte_string, self.countgekis = get_short(byte_string)
        byte_string, self.countkatus = get_short(byte_string)
        byte_string, self.countmisses = get_short(byte_string)

        byte_string, self.final_score = get_integer(byte_string)
        byte_string, self.max_combo = get_short(byte_string)
        byte_string, self.perfect = get_byte(byte_string)
        byte_string, self.mods = get_integer(byte_string)

        byte_string, life_graph = get_string(byte_string)
        if life_graph:
            self.life_graph = info_string_to_df(life_graph)
        else:
            self.life_graph = pd.DataFrame([[0, 0], [0, 0]])
        self.life_graph.columns = ["offset", "health"]

        byte_string, self.time_stamp = get_long(byte_string)

        byte_string, replay_length = get_integer(byte_string)
        self.replay, self.seed = lzma_replay_to_df(byte_string[:replay_length])
        self.replay_encoded = b64encode(byte_string[:replay_length])
        byte_string = byte_string[replay_length:]

        _, self.score_id = get_integer(byte_string)


def get_byte(byte_str):
    """
    Get a byte from byte string
    :param byte_str: byte string
    :return: byte string, byte
    """
    byte = byte_str[0]
    byte_str = byte_str[1:]
    return byte_str, byte


def get_short(byte_str):
    """
    Get a short from byte string
    :param byte_str: byte string
    :return: byte string, short
    """
    short = int.from_bytes(byte_str[:2], byteorder="little")
    byte_str = byte_str[2:]
    return byte_str, short


def get_integer(byte_str):
    """
    Get a integer from byte string
    :param byte_str: byte string
    :return: byte string, integer
    """
    integer = int.from_bytes(byte_str[:4], byteorder="little")
    byte_str = byte_str[4:]
    return byte_str, integer


def get_long(byte_str):
    """
    Get a long from byte string
    :param byte_str: byte string
    :return: byte string, long
    """
    long = int.from_bytes(byte_str[:8], byteorder="little")
    byte_str = byte_str[8:]
    return byte_str, long


def get_uleb128(byte_str):
    """
    Gets a unsigned leb128 number from byte sting
    :param byte_str: byte string
    :return: byte string, integer
    """
    uleb_parts = []
    while byte_str[0] >= 0x80:
        uleb_parts.append(byte_str[0] - 0x80)
        byte_str = byte_str[1:]
    uleb_parts.append(byte_str[0])
    byte_str = byte_str[1:]
    uleb_parts = uleb_parts[::-1]
    integer = 0
    for i in range(len(uleb_parts) - 1):
        integer = (integer + uleb_parts[i]) << 7
    integer += uleb_parts[-1]
    return byte_str, integer


def get_string(byte_str):
    """
    Get a string from byte string
    :param byte_str: byte string
    :return: byte string, string
    """
    byte_str, string_existence = get_byte(byte_str)
    if string_existence == 0:
        return byte_str, ""

    byte_str, length = get_uleb128(byte_str)
    string = str(byte_str[:length])[2:-1]
    byte_str = byte_str[length:]
    return byte_str, string


def calculate_unstable_rate(replay_dataframe, beatmap_obj, speed=1):
    pass
    # TODO


def get_action_at_time(dataframe, time):
    """
    Gives the closest entry in a dataframe rounded down in a replay dataframe
    :param dataframe: pandas dataframe
    :param time: time in milliseconds
    :return: dataframe entry
    """
    time = max(time, dataframe["offset"].iloc[0])
    time = min(time, dataframe["offset"].iloc[-1])
    exact_match = dataframe[dataframe["offset"] == time]
    if not exact_match.empty:
        index = exact_match.index[0]
    else:
        index = dataframe["offset"][dataframe["offset"] < time].idxmax()

    """lower = dataframe.iloc[index]
    upper = dataframe.iloc[index+1]
    perc = (time-lower["offset"])/(upper["offset"]-lower["offset"])
    dist = upper - lower"""
    # todo: smart interpolation

    return dataframe.iloc[index]


class SliderCurve:
    """
    slider curve object
    :param points: all cords of points on slider
    :param slider_type: slider type
    :param resolution: --optional-- resolution default: 200
    """

    def __init__(self, points, slider_type, resolution=None):
        if resolution is None:
            resolution = 200
        if slider_type == "L":
            resolution = 2

        if slider_type != "C":
            if slider_type == "B":
                points_list = split_on_double(points)
            else:
                points_list = [points]
            paths = list()
            for i in points_list:
                nodes = np.asfortranarray(i).transpose()
                paths.append(bezier.Curve.from_nodes(nodes))

            curve = list()
            for i in paths:
                s_v = np.linspace(0, 1, resolution)
                curve.append(i.evaluate_multi(s_v).transpose())
            for i, j in enumerate(curve[:-1]):
                curve[i] = j[:-1]
            self.curve = np.concatenate(curve)

            self.length = sum([i.length for i in paths])

            self.paths = list()
            per = 0
            for i in paths:
                self.paths.append((per, i))
                per += i.length / self.length

    def get_point(self, percentage):
        """
        get cords on slider
        :param percentage: percentage along slider
        :return: cords
        """
        clost = self.paths[0][1]
        clostper = 0
        for i, j in self.paths:
            if percentage >= i >= clostper:
                clostper = i
                clost = j

        loc = (percentage * self.length - clostper * self.length) / clost.length
        return clost.evaluate(loc)


def split_on_double(item_list):
    """
    split list every time a element is doubled
    :param item_list: list
    :return: list of lists
    """
    last = item_list[0]
    l_index = 0
    split_list = list()
    for i, j in list(enumerate(item_list))[1:]:
        if j == last:
            split_list.append(item_list[l_index:i])
            l_index = i
        last = j
    split_list.append(item_list[l_index:])
    return split_list


class ScoreReplay:
    def __init__(self, beatmap_obj, replay):
        beat_durations = dict()
        last_non = 1000
        beatmap_obj.timing_points[0].time = 0
        for i in beatmap_obj.timing_points:
            if i.ms_per_beat > 0:
                last_non = i.ms_per_beat
                duration = i.ms_per_beat
            else:
                duration = last_non * abs(i.ms_per_beat) / 100
            beat_durations[i.time] = duration

        self.objects = list()
        for i in beatmap_obj.hitobjects:
            duration = [j for j in beat_durations if j <= i.time][-1]
            if i.typestr() == "circle":
                self.objects.append({"type": "circle", "time": i.time,
                                     "position": (i.data.pos.x, i.data.pos.y)})
            elif i.typestr() == "spinner":
                self.objects.append({"type": "spinner", "time": i.time, "duration": i.data.end_time})
            else:
                slider_duration = i.data.distance / (100.0 * beatmap_obj.sv) \
                                  * beat_durations[duration]
                slider = SliderCurve([(i.data.pos.x, i.data.pos.y)]
                                     + [(a.x, a.y) for a in i.data.points], i.data.type)
                self.objects.append({"type": "slider", "time": i.time, "slider": slider,
                                     "repetitions": i.data.repetitions, "duration": slider_duration,
                                     "tick rate": beatmap_obj.tick_rate})
