import io
import math
from textwrap import wrap
from time import strftime, gmtime

import bezier
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image
from matplotlib import pyplot as plt

from ..utils import Log


def graph_bpm(map_obj):
    """
    graphs the bpm changes on map

    :param map_obj: a MapStats object
    :return: image in io stream
    """

    Log.log(f"Graphing BPM for {map_obj.title}")

    data = [(i.starttime / map_obj.speed_multiplier,
             1000 / i.ms_per_beat * 60 / map_obj.speed_multiplier)
            for i in map_obj.beatmap.timingpoints if i.change]

    chart_points = list()
    for i, j in enumerate(data):
        if i != 0:
            last = data[i - 1]
            chart_points.append((j[0] - .01, last[1]))
        chart_points.append(j)
        if len(data) - 1 == i:
            chart_points.append((map_obj.beatmap.hitobjects[-1].starttime
                                 / map_obj.speed_multiplier, j[1]))

    points = pd.DataFrame(chart_points)
    points.columns = ["Time", "BPM"]

    col = (38 / 255, 50 / 255, 59 / 255, .9)
    sns.set(rc={'axes.facecolor': col,
                'text.color': (236 / 255, 239 / 255, 241 / 255),
                'figure.facecolor': col,
                'savefig.facecolor': col,
                'xtick.color': (176 / 255, 190 / 255, 197 / 255),
                'ytick.color': (176 / 255, 190 / 255, 197 / 255),
                'grid.color': (69 / 255, 90 / 255, 100 / 255),
                'axes.labelcolor': (240 / 255, 98 / 255, 150 / 255),
                'xtick.bottom': True,
                'xtick.direction': 'in',
                'figure.figsize': (6, 4),
                'savefig.dpi': 100
                })

    ax = sns.lineplot(x="Time", y="BPM", data=points, color=(240 / 255, 98 / 255, 150 / 255))

    length = int(map_obj.total_length) * 1000
    m = length / 50
    plt.xlim(-m, length + m)

    formatter = matplotlib.ticker.FuncFormatter(lambda ms, x: strftime('%M:%S', gmtime(ms // 1000)))
    ax.xaxis.set_major_formatter(formatter)

    comp = round(max(1, (map_obj.bpm_max - map_obj.bpm_min) / 20), 2)
    top = round(map_obj.bpm_max, 2) + comp
    bot = max(round(map_obj.bpm_min, 2) - comp, 0)
    dist = top - bot

    plt.yticks(np.arange(bot, top, dist / 6 - .0001))

    plt.ylim(bot, top)

    round_num = 0 if dist > 10 else 2

    formatter = matplotlib.ticker.FuncFormatter(lambda dig, y:
                                                f"{max(dig - .004, 0.0):.{round_num}f}")
    ax.yaxis.set_major_formatter(formatter)

    ax.xaxis.grid(False)
    width = 85
    map_text = "\n".join(wrap(f"{map_obj.title} by {map_obj.artist}", width=width)) + "\n" + \
               "\n".join(wrap(f"Mapset by {map_obj.creator}, "
                              f"Difficulty: {map_obj.version}", width=width))
    plt.title(map_text)

    plt.box(False)

    image = io.BytesIO()
    plt.savefig(image, bbox_inches='tight')
    image.seek(0)

    plt.clf()
    plt.close()
    return image


def map_strain_graph(map_strains, progress=1., width=399., height=40., max_chunks=100, low_cut=30.):
    """
    generats a strains graph based on map

    :param map_strains: get_strains object
    :param progress: how much of the map player finished
    :param width: width of image
    :param height: height of image
    :param max_chunks: resolution to get out of map
    :param low_cut: adds some beefing to the bottem
    :return: an image in a bytesio object
    """

    strains, max_strain = map_strains["strains"], map_strains["max_strain"]

    strains_chunks = list()
    chunk_size = math.ceil(len(strains) / max_chunks)

    for i in range(0, len(strains), chunk_size):
        strain_part = strains[i:i + chunk_size]
        strains_chunks.append(max(strain_part))

    x = np.linspace(0, width, num=len(strains_chunks))
    y = np.minimum(low_cut,
                   height * 0.125 + height * .875 - np.array([i / max_strain for i in
                                                              strains_chunks]) * height * .875)

    x = np.insert(x, 0, 0)
    x = np.insert(x, 0, 0)
    x = np.append(x, width)
    x = np.append(x, width)
    y = np.insert(y, 0, low_cut)
    y = np.insert(y, 0, low_cut)
    y = np.append(y, low_cut)
    y = np.append(y, low_cut)
    curves = list()
    curves.append(bezier.Curve(np.asfortranarray([[0.0, 0.0], [height, low_cut]]), degree=1))
    for i in range(1, len(y) - 1):
        node = np.asfortranarray([
            [avgpt(x, i - 1), x[i], avgpt(x, i)],
            [avgpt(y, i - 1), y[i], avgpt(y, i)]])
        curves.append(
            bezier.Curve(node, degree=2)
        )
    curves.append(bezier.Curve(np.asfortranarray([[width, width], [low_cut, height]]), degree=1))
    curves.append(bezier.Curve(np.asfortranarray([[width, 0.0], [height, height]]), degree=1))
    polygon = bezier.CurvedPolygon(*curves)

    _, ax = plt.subplots(figsize=(round(width * 1.30), round(height * 1.30)), dpi=1)
    polygon.plot(pts_per_edge=200, color=(240 / 255, 98 / 255, 146 / 255, 1), ax=ax)
    plt.xlim(0, width)
    plt.ylim(height, 0)
    plt.axis('off')
    plt.box(False)

    image = io.BytesIO()
    fig1 = plt.gcf()
    fig1.savefig(image, bbox_inches='tight', transparent=True, pad_inches=0, dpi=1)
    image.seek(0)
    plt.clf()
    plt.close()

    img = Image.open(image)
    data = np.array(img)
    for j in data:
        for pos, i in enumerate(j):
            if pos > len(j) * progress:
                j[pos] = i / 1.5

            if i[3] != 0:
                j[pos][3] = i[3] / 159 * 255

    img = Image.fromarray(data)
    image.close()
    image = io.BytesIO()
    img.save(image, "png")
    image.seek(0)

    return image


def avgpt(points, index):
    """
    get the average between current point and the next one
    :param points: list of points
    :param index: index
    :return: average
    """
    return (points[index] + points[index + 1]) / 2.0
