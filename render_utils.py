"""
Module for rendering replays
"""
import subprocess
from os import remove

import gizeh
import moviepy.editor as mpy
import numpy as np
import pandas as pd

from osu_utils import speed_multiplier, CalculateMods
# speed_multiplier = CalculateMods=None
from replay_parser import get_action_at_time, SliderCurve, index_at_value

DIST_BEFORE = 100
DIST_AFTER = 10

WIDTH = 512
HEIGHT = 384

PADDING = 64

COLORS = [
    [255, 255, 255],  # [45,45,45]
    [197, 97, 26],
    [112, 197, 104],
    [200, 77, 223],
    [33, 122, 137]
]

COLORS = list(map(lambda x: [i / 255 for i in x], COLORS))


def for_approach_rate(approach_rate):
    """
    for a approach rate get how much before the circle appers and when it has full opacity
    :param approach_rate: float ar
    :return: preempt in ms, fade time in ms
    """
    if approach_rate < 5:
        preempt = 1200 + 600 * (5 - approach_rate) / 5
        fade_in = 800 + 400 * (5 - approach_rate) / 5
    elif approach_rate > 5:
        preempt = 1200 - 750 * (approach_rate - 5) / 5
        fade_in = 800 - 500 * (approach_rate - 5) / 5
    else:
        preempt = 1200
        fade_in = 800
    return preempt, fade_in


class HitCircle:
    """
    hit circle object
    :param time: start time
    :param position: position
    :param radius: circle radius
    :param color: circle color
    :param border: border color
    :param ar_ms: how fast circle appears
    :param fade_ms: when is it fully opaque
    """

    def __init__(self, time, position, radius, color, border, ar_ms, fade_ms):
        self.appear = time - ar_ms
        self.disappear = time + (ar_ms / DIST_AFTER)
        self.action = time
        self.border = border
        self.position = list(map(lambda x: x + PADDING, position))
        self.radius = radius
        self.color = color
        self.visable = False
        self.fade_ms = fade_ms
        self.ar_ms = ar_ms

    def render(self, time):
        """
        create gizeh object
        :param time: current time
        :return: gizeh object
        """
        alph = get_alpha(self, time)
        circle = gizeh.circle(self.radius - 5, xy=self.position,
                              stroke=(*self.border, alph), stroke_width=5, fill=(*self.color, alph))
        appr_circle = approach_circle(self, time)
        return [circle, appr_circle]


class Spinner:
    """
    spinner object
    :param time: start time
    :param end_time: end time
    :param color: color
    :param radius: circle radius
    :param ar_ms: how much before it appears
    :param fade_ms: when is it fully opaque
    """

    def __init__(self, time, end_time, color, radius, ar_ms, fade_ms):
        self.appear = time - ar_ms
        self.action = time
        self.radius = radius
        self.disappear = end_time
        pos = [WIDTH / 2, HEIGHT / 2]
        self.position = list(map(lambda x: x + PADDING, pos))
        self.visable = False
        self.color = color
        self.fade_ms = fade_ms
        self.ar_ms = ar_ms

    def approach_circle(self, time):
        """
        gets radius
        :param time: current time
        :return: radius
        """
        return max(min(self.radius,
                       -self.radius * ((time - self.action) / (self.disappear - self.action) - 1)),
                   0) + 9

    def render(self, time):
        """
        create gizeh object
        :param time: current time
        :return: gizeh object
        """
        alph = get_alpha(self, time)
        center = gizeh.circle(9, xy=self.position, fill=(1, 1, 1, alph))
        spinn = gizeh.circle(self.approach_circle(time), xy=self.position,
                             stroke_width=17, stroke=(*self.color, alph))
        return [center, spinn]


class Slider:
    """
    slider object
    :param time: start time
    :param position: position
    :param radius: circle radius
    :param distance: length of slider
    :param repetitions: how many repetitions
    :param slider_type: slider type
    :param points: slider points
    :param beat_duration: beat duration
    :param slider_vel: slider velocity
    :param color: slider color
    :param border: border color
    :param ar_ms: how much before it appears
    :param fade_ms: when is it fully opaque
    :param tick_rate: tick rate
    """

    def __init__(self, time, position, radius, distance, repetitions, slider_type,
                 points, beat_duration, slider_vel, color, border, ar_ms, fade_ms, tick_rate):
        slider_duration = distance / (100.0 * slider_vel) * beat_duration
        self.appear = time - ar_ms
        self.disappear = time + slider_duration * repetitions
        self.action = time
        self.duration = slider_duration
        self.repetitions = repetitions
        position = list(map(lambda x: x + PADDING, position))
        self.position = position
        self.radius = radius - 5
        self.points = [(i.x + PADDING, i.y + PADDING) for i in points]
        self.visable = False
        self.color = color
        self.border = border
        self.fade_ms = fade_ms
        self.ar_ms = ar_ms
        self.tick_rate = tick_rate
        self.slider = SliderCurve([tuple(self.position)] + self.points, slider_type)

    def slide(self, alpha):
        """
        create gizeh object
        :param alpha: current alpha
        :return: gizeh object
        """
        sld = map(lambda x: x * .9, self.color)
        slider = gizeh.polyline(points=self.slider.curve, stroke_width=self.radius * 2 + 5,
                                stroke=(*sld, alpha * .7), line_cap="round", line_join="round")
        return slider

    def ball(self, time, alpha):
        """
        create gizeh object
        :param time: current time
        :param alpha: current alpha
        :return: gizeh object
        """
        time_strt = min(max(self.action, time) - self.action, self.duration * self.repetitions)
        per = time_strt % (self.duration + 1) / self.duration
        if time_strt / self.duration % 2 > 1:
            per = 1 - per
        pos = self.slider.get_point(per)
        bll = map(lambda x: x * .4, self.color)
        alph = alpha if time < self.action else 0
        ball = gizeh.circle(self.radius, xy=pos, fill=(*bll, alpha),
                            stroke=(*self.border, alph), stroke_width=5)

        return ball

    def render(self, time):
        """
        create gizeh object
        :param time: current time
        :return: gizeh object
        """
        alph = get_alpha(self, time)
        slide = self.slide(alph)
        ball = self.ball(time, alph)
        appr_circle = approach_circle(self, time)
        return [slide, appr_circle, ball]


def get_alpha(self, time):
    """
    get alpha object should have
    :param self: object
    :param time: current time
    :return: alpha float
    """
    return min(1, max(0, (time - self.appear) / self.fade_ms))


def approach_circle(self, time):
    """
    create gizeh object
    :param self: object
    :param time: current time
    :return: gizeh object
    """
    rad = self.radius + max(0, (self.action - time) / (self.ar_ms / DIST_BEFORE))
    alpha = 0.15 if rad == self.radius else get_alpha(self, time)
    return gizeh.circle(rad, xy=self.position, stroke_width=5, stroke=(1, 1, 1, alpha))


class Replay:
    """
    replay object for rendering
    :param beatmap_obj: beatmap object
    :param replay_dataframe: replay pandas dataframe
    :param mods: mods applied
    :param combo_colors: --optional-- colors
    """

    def __init__(self, beatmap_obj, replay_dataframe, mods=[], combo_colors=None):
        if combo_colors is None:
            combo_colors = COLORS
        self.mods = mods
        self.speed = speed_multiplier(mods)
        aug = CalculateMods([i for i in mods if i not in ["DT", "HT", "NC"]])
        self.approach_rate, _, _ = aug.ar(beatmap_obj.ar)
        self.circle_size, _ = aug.cs(beatmap_obj.cs)
        self.border = combo_colors[0]
        self.colors = combo_colors[1:]
        self.minimum = abs(min(0, replay_dataframe["offset"].min()))
        self.replay = replay_dataframe
        self.beatmap = beatmap_obj
        self.tick_rate = beatmap_obj.tick_rate

        self.circle_radius = (WIDTH / 16) * (1 - (0.7 * (self.circle_size - 5) / 5))
        self.spinner_radius = HEIGHT * .85 / 2
        self.ar_ms, self.fade_ms = for_approach_rate(self.approach_rate)
        self.beat_durations = dict()
        last_non = 1000
        beatmap_obj.timing_points[0].time = 0
        for i in beatmap_obj.timing_points:
            if i.ms_per_beat > 0:
                last_non = i.ms_per_beat
                duration = i.ms_per_beat
            else:
                duration = last_non * abs(i.ms_per_beat) / 100
            self.beat_durations[i.time] = duration

        objects = list()
        col = -1
        for i in beatmap_obj.hitobjects:
            if i.objtype & (1 << 2):
                col += 1
            if i.objtype & (1 << 4):
                col += (16 >> 4)
            if i.objtype & (1 << 5):
                col += (32 >> 4)
            if i.objtype & (1 << 6):
                col += (64 >> 4)
            col = col % len(self.colors)

            duration = [j for j in self.beat_durations if j <= i.time][-1]
            if i.typestr() == "circle":
                objects.append(HitCircle(i.time, (i.data.pos.x, i.data.pos.y),
                                         self.circle_radius, self.colors[col],
                                         self.border, self.ar_ms, self.fade_ms))
            elif i.typestr() == "spinner":
                objects.append(Spinner(i.time, i.data.end_time, self.border,
                                       self.spinner_radius, self.ar_ms, self.fade_ms))
            else:
                objects.append(
                    Slider(i.time, (i.data.pos.x, i.data.pos.y), self.circle_radius,
                           i.data.distance, i.data.repetitions, i.data.type, i.data.points,
                           self.beat_durations[duration], beatmap_obj.sv, self.colors[col],
                           self.border, self.ar_ms, self.fade_ms, self.tick_rate))
        self.objects = objects[::-1]

        self.offset = 0

    def make_frame(self, time_decimal):
        """
        render frame
        :param time_decimal: time in seconds
        :return: 3d numpy array
        """
        time_decimal = time_decimal + self.offset
        time = time_decimal * 1000 - self.minimum
        surface = gizeh.Surface(WIDTH + PADDING * 2, HEIGHT + PADDING * 2)
        cords = get_action_at_time(self.replay, time)

        left = (.2, 0, 0)
        right = (.2, 0, 0)

        click = cords["clicks"]
        if click in [1, 5, 15]:
            left = (.9, 0, 0)
        if click in [2, 10, 15]:
            right = (.9, 0, 0)

        size_multiplier = 1.15 if click else 1
        mouse = gizeh.circle(10 * size_multiplier, xy=(cords["x pos"] + PADDING,
                                                       cords["y pos"] + PADDING),
                             fill=(1, 0, 0), stroke=(0, 1, 0), stroke_width=2)

        sqrl = gizeh.square(l=30, fill=left, xy=(surface.width - 60, surface.height - 24))
        sqrr = gizeh.square(l=30, fill=right, xy=(surface.width - 25, surface.height - 24))
        clicks = gizeh.Group([sqrl, sqrr])

        render_objects = list()
        for i in self.objects:
            if i.appear <= time:
                i.visable = True
            if i.disappear <= time:
                i.visable = False

            if i.visable:
                render_objects.extend(i.render(time))
        hit_objects = gizeh.Group(render_objects)

        hit_objects.draw(surface)
        mouse.draw(surface)
        clicks.draw(surface)
        return surface.get_npimage()

    def render(self, name, start_offset, duration, fps=30, audio=None):
        """
        render object
        :param name: file to save as
        :param start_offset: where to start
        :param duration: how long the clip will be
        :param fps: default: 30
        :param audio: audio file path
        :return: None. saves file
        """
        self.offset = start_offset
        clip = mpy.VideoClip(self.make_frame, duration=duration * self.speed).speedx(self.speed)
        if audio is not None:
            subprocess.run(["ffmpeg", "-loglevel", "quiet", "-i", audio, "-filter:a",
                            f"atempo={self.speed}", "-vn", f"{audio}.mp3"])
            audio = f"{audio}.mp3"
            audio_start_offset = start_offset
            acl = mpy.AudioFileClip(audio)
            blnk = mpy.AudioClip(lambda x: 0, duration=self.minimum / 1000)
            aftr = max(0, (duration + audio_start_offset) - acl.duration)
            ablnk = mpy.AudioClip(lambda x: 0, duration=aftr)
            snd = mpy.concatenate_audioclips([blnk, acl, ablnk])
            clip = clip.set_audio(snd.subclip(audio_start_offset, duration + audio_start_offset))
            remove(audio)

        if name.endswith(".gif"):
            clip.write_gif(name, fps=fps)
            subprocess.run(
                ["../gifsicle-1.82.1-lossy/mac/gifsicle", "-O3", "--lossy=30", "-o",
                 "circle.gif", "circle.gif"])
        else:
            clip.write_videofile(name, fps=fps)


def perfect_play(beatmap_obj):
    """
    given a beatmap object generate a perfect play
    :param beatmap_obj: beatmap object
    :return: pandas dataframe play
    """
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

    objects = list()
    for i in beatmap_obj.hitobjects:
        duration = [j for j in beat_durations if j <= i.time][-1]
        if i.typestr() == "circle":
            objects.append({"type": "circle", "time": i.time,
                            "position": (i.data.pos.x, i.data.pos.y)})
        elif i.typestr() == "spinner":
            objects.append({"type": "spinner", "time": i.time, "duration": i.data.end_time})
        else:
            slider_duration = i.data.distance / (100.0 * beatmap_obj.sv) \
                              * beat_durations[duration]
            slider = SliderCurve([(i.data.pos.x, i.data.pos.y)]
                                 + [(a.x, a.y) for a in i.data.points], i.data.type)
            objects.append({"type": "slider", "time": i.time, "slider": slider,
                            "repetitions": i.data.repetitions, "duration": slider_duration})

    last_click = 10
    first_offset = objects[0]["time"] - 2000
    if objects[-1]["type"] == "spinner":
        last_offset = objects[-1]["duration"] + 2000
    elif objects[-1]["type"] == "slider":
        last_offset = objects[-1]["duration"] + objects[-1]["time"] + 2000
    else:
        last_offset = objects[-1]["time"] + 2000
    safzon = 70
    play = pd.DataFrame([[int(i), np.nan, np.nan, 0] for i in np.arange(first_offset, last_offset, 17)],
                        columns=["offset", "x pos", "y pos", "clicks"])

    play.loc[0, ["x pos", "y pos"]] = [WIDTH / 2, HEIGHT / 2]

    for i in objects:
        if last_click == 10:
            last_click = 5
        else:
            last_click = 10

        if i["type"] == "circle":
            for j in np.arange(i["time"], i["time"] + 80, 17):
                index = index_at_value(play, j, "offset")
                play.iloc[index] = [int(j), *i["position"], last_click]

        elif i["type"] == "slider":
            items = list()
            for j in i["slider"].curve:
                dst = j - i["slider"].curve[0]
                items.append(np.sqrt(dst[0] ** 2 + dst[1] ** 2))
            series = pd.Series(items)
            for j in np.arange(i["time"], i["time"] + i["duration"] * i["repetitions"], 17):
                if series[series > safzon].any():
                    time_start = min(max(i["time"], j) - i["time"],
                                     i["duration"] * i["repetitions"])
                    per = time_start % (i["duration"] + 1) / i["duration"]
                    if time_start / i["duration"] % 2 > 1:
                        per = 1 - per
                    pos = i["slider"].get_point(per)
                else:
                    pos = i["slider"].get_point(0)

                index = index_at_value(play, j, "offset")
                play.iloc[index] = [int(j), *[r[0] for r in pos], last_click]

        elif i["type"] == "spinner":
            for j in np.arange(i["time"], i["duration"], 17):
                xpos = -np.math.sin(j / 30) * 50 + 512 / 2
                ypos = np.math.cos(j / 30) * 50 + 384 / 2

                index = index_at_value(play, j, "offset")
                play.iloc[index] = [int(j), xpos, ypos, last_click]

    play.loc[-1, ["x pos", "y pos"]] = [WIDTH / 2, HEIGHT / 2]

    return play.interpolate()
