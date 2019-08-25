import gizeh
import moviepy.editor as mpy
from replayParser import get_action_at_time
import bezier
import numpy as np
import subprocess

dist_before = 100
dist_after = 10

width = 512
height = 384

padding = 64

res = 200

colors = [
    [197, 97, 26],
    [112, 197, 104],
    [200, 77, 223],
    [33, 122, 137]
]

border = [1, 1, 1]  # [45/255,45/255,45/255]

colors = list(map(lambda x: [i / 255 for i in x], colors))


def ar(approach_rate):
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
    def __init__(self, time, position, radius, color, ar_ms, fade_ms):
        self.appear = time - ar_ms
        self.disappear = time + (ar_ms / dist_after)
        self.action = time
        self.position = list(map(lambda x: x + padding, position))
        self.radius = radius
        self.color = color
        self.visable = False
        self.fade_ms = fade_ms
        self.ar_ms = ar_ms

    def render(self, time):
        alph = get_alpha(self, time)
        circle = gizeh.circle(self.radius - 5, xy=self.position,
                              stroke=(*border, alph), stroke_width=5, fill=(*self.color, alph))
        appr_circle = approach_circle(self, time)
        return [circle, appr_circle]


class Spinner:
    def __init__(self, time, end_time, color, radius, ar_ms, fade_ms):
        self.appear = time - ar_ms
        self.action = time
        self.radius = radius
        self.disappear = end_time
        pos = [width / 2, height / 2]
        self.position = list(map(lambda x: x + padding, pos))
        self.visable = False
        self.color = color
        self.fade_ms = fade_ms
        self.ar_ms = ar_ms

    def approach_circle(self, time):
        return min(self.radius, 9 + abs(-(1 - time / self.disappear) * self.radius * 2))

    def render(self, time):
        alph = get_alpha(self, time)
        center = gizeh.circle(9, xy=self.position, fill=(1, 1, 1, alph))
        spinn = gizeh.circle(self.approach_circle(time), xy=self.position, stroke_width=17, stroke=(1, 1, 1, alph))
        return [center, spinn]


class Slider:
    def __init__(self, time, position, radius, distance, repetitions, slider_type,
                 points, beat_duration, slider_vel, color, ar_ms, fade_ms, tick_rate):
        slider_duration = distance / (100.0 * slider_vel) * beat_duration
        self.appear = time - ar_ms
        self.disappear = time + slider_duration * repetitions
        self.action = time
        self.duration = slider_duration
        self.repetitions = repetitions
        position = list(map(lambda x: x + padding, position))
        self.position = position
        self.radius = radius - 5
        self.points = [(i.x + padding, i.y + padding) for i in points]
        self.visable = False
        self.color = color
        self.type = slider_type
        self.fade_ms = fade_ms
        self.ar_ms = ar_ms
        self.tick_rate = tick_rate

    def slide(self, alpha):
        slider = gizeh.circle(0)
        if self.type in ["B", "L", "P"]:
            nodes = [tuple(self.position)] + self.points
            nodes = np.asfortranarray(nodes).transpose()
            curv = bezier.Curve(nodes, len(self.points) + 1)
            s_v = np.linspace(0, 1, res)
            pos = curv.evaluate_multi(s_v).transpose()
            sld = map(lambda x: x * .9, self.color)
            slider = gizeh.polyline(points=pos, stroke_width=self.radius * 2 + 5, stroke=(*sld, alpha),
                                    line_cap="round", line_join="round")
        return slider

    def ball(self, time, alpha):
        ball = gizeh.circle(0)
        if self.type in ["B", "L", "P"]:
            nodes = [tuple(self.position)] + self.points
            nodes = np.asfortranarray(nodes).transpose()
            curv = bezier.Curve(nodes, len(self.points) + 1)
            time_strt = min(max(self.action, time) - self.action, self.duration * self.repetitions)
            per = time_strt % (self.duration + 1) / self.duration
            if time_strt / self.duration % 2 > 1:
                per = 1 - per
            pos = curv.evaluate(per)
            bll = map(lambda x: x * .4, self.color)
            alph = alpha if time < self.action else 0
            ball = gizeh.circle(self.radius, xy=pos, fill=(*bll, alpha),
                                stroke=(*border, alph), stroke_width=5)

        return ball

    def render(self, time):
        alph = get_alpha(self, time)
        slide = self.slide(alph)
        ball = self.ball(time, alph)
        appr_circle = approach_circle(self, time)
        return [slide, appr_circle, ball]


def get_alpha(self, time):
    return min(1, max(0, (time - self.appear) / self.fade_ms))


def approach_circle(self, time):
    rad = self.radius + max(0, (self.action - time) / (self.ar_ms / dist_before))
    alpha = 0.15 if rad == self.radius else get_alpha(self, time)
    return gizeh.circle(rad, xy=self.position, stroke_width=5, stroke=(1, 1, 1, alpha))


class Replay:
    def __init__(self, beatmap_obj, replay_dataframe, combo_colors=None):
        if combo_colors is None:
            combo_colors = colors
        self.colors = combo_colors
        self.minimum = abs(min(0, replay_dataframe["offset"].min()))
        self.replay = replay_dataframe
        self.beatmap = beatmap_obj
        self.tick_rate = beatmap_obj.tick_rate

        self.circle_radius = (width / 16) * (1 - (0.7 * (beatmap_obj.cs - 5) / 5))
        self.spinner_radius = height * .85 / 2
        self.ar_ms, self.fade_ms = ar(beatmap_obj.ar)
        self.beat_durations = dict()
        last_non = 1000
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
            if i.objtype & 1 << 2:
                col += 1
            if i.objtype & 1 << 4:
                col += 16 >> 4
            if i.objtype & 1 << 5:
                col += 32 >> 4
            if i.objtype & 1 << 6:
                col += 64 >> 4
            col = col % len(colors)

            duration = [j for j in self.beat_durations.keys() if j <= i.time][-1]
            if i.typestr() == "circle":
                objects.append(HitCircle(i.time, (i.data.pos.x, i.data.pos.y),
                                         self.circle_radius, colors[col], self.ar_ms, self.fade_ms))
            elif i.typestr() == "spinner":
                objects.append(Spinner(i.time, i.data.end_time, colors[col],
                                       self.spinner_radius, self.ar_ms, self.fade_ms))
            else:
                objects.append(
                    Slider(i.time, (i.data.pos.x, i.data.pos.y), self.circle_radius, i.data.distance,
                           i.data.repetitions, i.data.type, i.data.points, self.beat_durations[duration],
                           beatmap_obj.sv, colors[col], self.ar_ms, self.fade_ms, self.tick_rate))
        self.objects = objects[::-1]

        self.offset = 0

    def make_frame(self, t):
        t = t + self.offset
        time = t * 1000
        surface = gizeh.Surface(width + padding * 2, height + padding * 2)
        cords = get_action_at_time(self.replay, time - self.minimum)

        left = (.2, 0, 0)
        right = (.2, 0, 0)

        click = cords["clicks"]
        if click == 5 or click == 1 or click == 15:
            left = (.9, 0, 0)
        if click == 10 or click == 2 or click == 15:
            right = (.9, 0, 0)

        bg = 1
        # bg = 1.3 if click else 1
        col = (1, 0, 0)
        col = (0, 1, 0) if click else (1, 0, 0)
        mouse = gizeh.circle(10 * bg, xy=(cords["x pos"] + padding, cords["y pos"] + padding), fill=col)

        sqrl = gizeh.square(l=30, fill=left, xy=(surface.width - 60, surface.height - 24))
        sqrr = gizeh.square(l=30, fill=right, xy=(surface.width - 25, surface.height - 24))
        clicks = gizeh.Group([sqrl, sqrr])

        renderObjs = list()
        for i in self.objects:
            if i.appear <= time:
                i.visable = True
            if i.disappear <= time:
                i.visable = False

            if i.visable:
                renderObjs.extend(i.render(time))
        circls = gizeh.Group(renderObjs)

        circls.draw(surface)
        mouse.draw(surface)
        clicks.draw(surface)
        return surface.get_npimage()

    def render(self, name, start_offset, duration, fps=30):
        self.offset = start_offset
        clip = mpy.VideoClip(self.make_frame, duration=duration)

        if name.endswith(".gif"):
            clip.write_gif(name, fps=fps)
            subprocess.run(
                ["../gifsicle-1.82.1-lossy/mac/gifsicle", "-O3", "--lossy=30", "-o", "circle.gif", "circle.gif"])
        else:
            clip.write_videofile(name, fps=fps, audio=False)
