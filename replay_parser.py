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


class DegenerateTriangle(Exception):
    pass


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


def index_at_value(dataframe, value, column):
    """
    get closet lower index closet to value
    :param dataframe: pandas dataframe
    :param value: value to search for
    :param column: column to search in
    :return: index
    """
    exact_match = dataframe[dataframe[column] == value]
    if not exact_match.empty:
        index = exact_match.index[0]
    else:
        index = dataframe[column][dataframe[column] < value].idxmax()

    return index


def get_action_at_time(dataframe, time):
    """
    Gives the closest entry in a dataframe rounded down in a replay dataframe
    :param dataframe: pandas dataframe
    :param time: time in milliseconds
    :return: dataframe entry
    """
    time = max(time, dataframe.iloc[0].loc["offset"])
    time = min(time, dataframe.iloc[-1].loc["offset"])
    index = index_at_value(dataframe, time, "offset")

    """lower = dataframe.iloc[index]
    upper = dataframe.iloc[index+1]
    perc = (time-lower["offset"])/(upper["offset"]-lower["offset"])
    dist = upper - lower"""
    # todo: smart interpolation

    return dataframe.loc[index]


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
            if slider_type == "P":
                try:
                    paths.append(PerfectSlider(points))
                except DegenerateTriangle:
                    for i in points_list:
                        nodes = np.asfortranarray(i).transpose()
                        paths.append(bezier.Curve.from_nodes(nodes))
            else:
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


class PerfectSlider:
    def __init__(self, points):
        points = np.array(points)
        self.center, self.radius = get_circumcircle(points)
        min_theta = np.arctan2(points[0][1] - self.center[1], points[0][0] - self.center[0])
        max_theta = np.arctan2(points[2][1] - self.center[1], points[2][0] - self.center[0])
        pass_through = np.arctan2(points[1][1] - self.center[1], points[1][0] - self.center[0])

        mi = (min_theta + np.pi * 2) % (np.pi * 2)
        ma = (max_theta + np.pi * 2) % (np.pi * 2)
        pa = (pass_through + np.pi * 2) % (np.pi * 2)

        p2 = (points[2][1] - self.center[1], points[2][0] - self.center[0])
        p1 = (points[0][1] - self.center[1], points[0][0] - self.center[0])
        if not mi < pa < ma:
            dist = np.arctan2(*p2) - np.arctan2(*p1)
        else:
            dist = np.pi * 2 - (np.arctan2(*p1) - np.arctan2(*p2))

        self.min_theta = min_theta
        self.length = abs(dist)
        self.dist = dist

    def evaluate(self, percentage):
        theta = percentage * self.dist + self.min_theta
        data = np.ndarray(shape=(2, 1), dtype=float)

        data[0][0] = self.center[0] + self.radius * np.cos(theta)
        data[1][0] = self.center[1] + self.radius * np.sin(theta)

        return data

    def evaluate_multi(self, s_v):
        pn = np.array(list(map(self.evaluate, s_v)))

        return pn.transpose()[0]


def get_circumcircle(triangle):
    assert triangle.shape == (3, 2)

    aSq = distance(triangle[1] - triangle[2]) ** 2
    bSq = distance(triangle[0] - triangle[2]) ** 2
    cSq = distance(triangle[0] - triangle[1]) ** 2

    if almost_equals(aSq, 0) or almost_equals(bSq, 0) or almost_equals(cSq, 0):
        raise DegenerateTriangle

    s = aSq * (bSq + cSq - aSq)
    t = bSq * (aSq + cSq - bSq)
    u = cSq * (aSq + bSq - cSq)

    if almost_equals(sum([s, u, t]), 0):
        raise DegenerateTriangle

    line1 = perpendicular_line(triangle[1], triangle[0])
    line2 = perpendicular_line(triangle[1], triangle[2])

    coef1 = line1.coeffs
    coef2 = line2.coeffs

    x_center = (coef1[1] - coef2[1]) / (coef2[0] - coef1[0])
    y_center = line1(x_center)
    center = np.array([x_center, y_center])

    dist = triangle[0] - center
    radius = distance(dist)
    return center, radius


def perpendicular_line(point1, point2):
    center = (point1 + point2) / 2
    slope_diff = point1 - point2
    if 0 in slope_diff:
        slope_diff += 1e-10
        # raise DegenerateTriangle
    slope = slope_diff[1] / slope_diff[0]
    new_slope = -1 / slope
    offset = center[1] - new_slope * center[0]
    return np.poly1d([new_slope, offset])


def almost_equals(value1, value2, acceptable_distance=None):
    if acceptable_distance is None:
        acceptable_distance = 1e-3

    return abs(value1 - value2) <= acceptable_distance


def distance(point):
    return np.sqrt(point[0] ** 2 + point[1] ** 2)


class ScoreReplay:
    def __init__(self, beatmap_obj, replay):
        beat_durations = dict()
        last_non = 1000
        beatmap_obj.timing_points[0].time = 0
        mspb = dict()
        for i in beatmap_obj.timing_points:
            if i.ms_per_beat > 0:
                last_non = i.ms_per_beat
                duration = i.ms_per_beat
                mspb[i.time] = i.ms_per_beat
            else:
                duration = last_non * abs(i.ms_per_beat) / 100
            beat_durations[i.time] = duration

        self.objects = list()
        for i in beatmap_obj.hitobjects:
            duration = [j for j in beat_durations if j <= i.time][-1]
            msperb = [v for j, v in mspb.items() if j <= i.time][-1]
            if i.typestr() == "circle":
                self.objects.append({"type": "circle", "time": i.time,
                                     "position": (i.data.pos.x, i.data.pos.y),
                                     "pressed": False})
            elif i.typestr() == "spinner":
                self.objects.append({"type": "spinner", "time": i.time, "end_time": i.data.end_time})
            else:
                slider_duration = i.data.distance / (100.0 * beatmap_obj.sv) \
                                  * beat_durations[duration]
                slider = SliderCurve([(i.data.pos.x, i.data.pos.y)]
                                     + [(a.x, a.y) for a in i.data.points], i.data.type)

                num_of_ticks = beatmap_obj.tick_rate * slider_duration / msperb
                ticks_once = {i: False for i in percent_positions(int(num_of_ticks))}
                ticks = {i + 1: ticks_once for i in range(i.data.repetitions)}
                for tickset in ticks.copy():
                    if tickset % 3 > 1:
                        ticks[tickset] = {1 - i: False for i in ticks[tickset]}
                endings = {i + 1: False for i in range(i.data.repetitions)}
                self.objects.append({"type": "slider", "time": i.time, "slider": slider,
                                     "speed": (100.0 * beatmap_obj.sv) * beat_durations[duration],
                                     "duration": slider_duration, "repetitions": i.data.repetitions,
                                     "start": False, "ticks": ticks, "end": endings})

        self.replay = replay
        self.score = pd.DataFrame(columns=["offset", "combo", "hit", "bonuses", "displacement", "object"])

        self.hit_window50 = 0
        self.hit_window100 = 0
        self.hit_window300 = 0

        self.k1 = 1 << 0
        self.k2 = 1 << 1

        self.circle_radius = 0
        self.follow_circle = 0

        self.speed = 1

        self.spins_per_second = 0
        self.compensate = replay["offset"].diff().median() / 2.5

    def generate_score(self, od, cs, speed=1, ms_compensate=None):
        self.score = pd.DataFrame(columns=["offset", "combo", "hit", "bonuses", "displacement", "object"])
        # calculate score and accuracy afterwords

        if ms_compensate is not None:
            self.compensate = ms_compensate

        self.speed = speed

        self.hit_window50 = (150 + 50 * (5 - od) / 5) + self.compensate
        self.hit_window100 = (100 + 40 * (5 - od) / 5) + self.compensate
        self.hit_window300 = (50 + 30 * (5 - od) / 5) + self.compensate

        self.circle_radius = (512 / 16) * (1 - (0.7 * (cs - 5) / 5))
        self.follow_circle = (512 / 16) * (1 - (0.5 * (cs - 5) / 7)) * 10

        if od > 5:
            self.spins_per_second = 5 + 2.5 * (od - 5) / 5
        elif od < 5:
            self.spins_per_second = 5 - 2 * (5 - od) / 5
        else:
            self.spins_per_second = 5

        for i in self.objects:
            if i["type"] == "circle":
                score_data = self.mark_circle(i)

            elif i["type"] == "spinner":
                score_data = self.mark_spinner(i)

            elif i["type"] == "slider":
                score_data = self.mark_slider(i)

            else:
                combo = 0.
                hit = 0.
                deviance = np.nan
                bonuses = 0.

                score_data = [i["time"], combo, hit, bonuses, deviance, i["type"]]

            self.score.at[len(self.score) + 1] = score_data

        return self.score

    def mark_circle(self, hit_circle, alternated_hit_window=1.):
        combo = self.get_combo()

        lower = self.replay[self.replay["offset"] >= hit_circle["time"]
                            - self.hit_window50 * alternated_hit_window]
        upper = lower[lower["offset"] <= hit_circle["time"] + self.hit_window50]
        key1 = False
        key2 = False
        offset = None
        deviance = None
        clicks = list()
        for j in upper.iterrows():
            time_action = j[1]
            last_key1 = key1
            last_key2 = key2
            key1 = int(time_action["clicks"]) & self.k1
            key2 = int(time_action["clicks"]) & self.k2
            if (not last_key1 and key1) or (not last_key2 and key2):
                if np.sqrt((time_action["x pos"] - hit_circle["position"][0]) ** 2 +
                           (time_action["y pos"] - hit_circle["position"][1]) ** 2) <= self.circle_radius:
                    hit_circle["pressed"] = True
                    if hit_circle["time"] - self.hit_window300 <= \
                            time_action["offset"] <= hit_circle["time"] + self.hit_window300:
                        clicks.append(time_action["offset"] - hit_circle["time"])

                    elif hit_circle["time"] - self.hit_window100 <= \
                            time_action["offset"] <= hit_circle["time"] + self.hit_window100:
                        clicks.append(time_action["offset"] - hit_circle["time"])

                    elif hit_circle["time"] - self.hit_window50 <= \
                            time_action["offset"] <= hit_circle["time"] + self.hit_window50:
                        clicks.append(time_action["offset"] - hit_circle["time"])
                    elif hit_circle["time"] - self.hit_window50 > time_action["offset"]:
                        offset = time_action["offset"]
                        hit_circle["pressed"] = False
                        deviance = time_action["offset"] - hit_circle["time"]
                        break
        if hit_circle["pressed"]:
            closet_click = min([(abs(i), i) for i in clicks])
            if closet_click[0] <= self.hit_window300:
                hit = 300.
            elif closet_click[0] <= self.hit_window100:
                hit = 100.
            else:
                hit = 50
            combo += 1.
            offset = closet_click[1] + hit_circle["time"]
            deviance = closet_click[1]
            bonuses = 0.
        else:
            combo = 0.
            if offset is None:
                offset = hit_circle["time"]
            hit = 0.
            if deviance is None:
                deviance = np.nan
            bonuses = 0.

        return offset, combo, hit, bonuses, deviance, hit_circle["type"]

    def mark_spinner(self, spinner):
        combo = self.get_combo()

        length = (spinner["end_time"] - spinner["time"]) / 1000
        required_spins = np.floor(self.spins_per_second * length * .55)

        lower = self.replay[self.replay["offset"] >= spinner["time"]]
        upper = lower[lower["offset"] <= spinner["end_time"]]
        hold = upper[upper["clicks"] != 0]

        x_pos = hold.loc[:, "x pos"] - 512 / 2
        y_pos = hold.loc[:, "y pos"] - 384 / 2
        d_theta = np.arctan2(y_pos, x_pos).diff() / np.pi * 180
        spins_index = (d_theta[abs(d_theta) > 200]).index
        spins = hold.loc[spins_index]

        rpm = pd.Series(name="rotations per minute")
        last_revolution = spinner["time"]
        for spin in spins.iterrows():
            rpm.at[spin[1]["offset"]] = spin[1]["offset"] - last_revolution
            last_revolution = spin[1]["offset"]
        extra_spin = hold.iloc[-1]["offset"] - spins.iloc[-1]["offset"]

        if len(rpm) >= required_spins:
            hit = 300.
            combo += 1.
            bonuses = 1000. * (len(rpm) - required_spins)
        elif len(rpm) + extra_spin / 360 >= required_spins / 2 * .5 + required_spins / 2:
            hit = 100.
            combo += 1.
            bonuses = 0.
        elif len(rpm) + extra_spin / 360 >= required_spins / 2:
            hit = 50.
            combo += 1.
            bonuses = 0.
        else:
            combo = 0.
            hit = 0.
            bonuses = 0.

        offset = spinner["time"]
        deviance = 1000 / rpm * 60 * self.speed

        return [offset, combo, hit, bonuses, deviance, spinner["type"]]

    def mark_slider(self, slider):
        combo = self.get_combo()

        slider_parts = pd.Series(name="data on slider")

        first_click = self.mark_circle({"type": "slider_start", "time": slider["time"],
                                        "position": [i[0] for i in slider["slider"].get_point(0)],
                                        "pressed": False}, 1.0075)
        if first_click[2] > 0 and 0 >= first_click[3]:
            slider["start"] = True
            combo += 1.
        else:
            combo = 0.
        slider_parts.at["slider start"] = slider["start"]

        slider_start = self.replay[self.replay["offset"] >= slider["time"]]
        slider_end = slider_start[slider_start["offset"] <= slider["time"]
                                  + slider["duration"] * slider["repetitions"]]
        for tickset in slider["ticks"]:
            for tick in slider["ticks"][tickset]:
                # tick_lower_time = slider_end[slider_end["offset"] >= slider["time"]
                #                              + slider["duration"] * tick
                #                              - self.circle_radius / slider["speed"]]
                # tick_upper_time = tick_lower_time[tick_lower_time["offset"] <= slider["time"]
                #                                   + slider["duration"] * tick
                #                                   + self.circle_radius / slider["speed"]]
                tick_slice = get_action_at_time(slider_end, slider["time"]
                                                + slider["duration"] * tick)

                if tick_slice["clicks"] > 0:
                    position = slider["slider"].get_point(tick)
                    if np.sqrt((tick_slice["x pos"] - position[0][0]) ** 2 +
                               (tick_slice["y pos"] - position[1][0]) ** 2) <= self.follow_circle:
                        slider["ticks"][tickset][tick] = True
                        combo += 1.
                        slider_parts.at[f"tick {tickset}:{tick * 100:.0f}"] = slider["ticks"][tickset][tick]
                        break
                combo = 0.
                slider_parts.at[f"{tickset}:{tick * 100:.0f}"] = slider["ticks"][tickset][tick]

        for slider_edge in slider["end"]:
            end_time = slider["time"] + slider["duration"] * slider_edge
            position = slider["slider"].get_point(slider_edge % 2)
            end_slice = get_action_at_time(slider_end, end_time)
            if np.sqrt((end_slice["x pos"] - position[0][0]) ** 2 +
                       (end_slice["y pos"] - position[1][0]) ** 2) <= self.follow_circle:
                if end_slice["clicks"]:
                    slider["end"][slider_edge] = True
                    combo += 1.
            if slider_edge != len(slider["end"]):
                if not slider["end"][slider_edge]:
                    combo = 0.
                slider_parts.at["slider repeat"] = slider["end"][slider_edge]
            else:
                slider_parts.at["slider end"] = slider["end"][len(slider["end"])]

        if slider_parts.all():
            hit = 300.
        elif len(slider_parts[slider_parts]) >= len(slider_parts) / 2:
            hit = 100.
        elif slider_parts.any():
            hit = 50.
        else:
            hit = 0.

        offset = slider["time"]
        deviance = slider_parts
        bonuses = 0.

        return offset, combo, hit, bonuses, deviance, slider["type"]

    def get_combo(self):
        previous_idx = max(0, len(self.score) - 1)
        return self.score.iloc[previous_idx]["combo"] if not self.score.empty else 0.

    def calculate_unstable_rate(self, speed=1):
        pass
        # TODO


def percent_positions(num_of_itms):
    percentages = list()
    for i in range(1, num_of_itms + 1):
        percentages.append(i / (num_of_itms + 1))
    return percentages
