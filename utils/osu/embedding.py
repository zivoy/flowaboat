from time import time

import arrow
import discord

from utils import SEPARATOR
from .stating import stat_play
from .utils import get_rank_emoji, sanitize_mods
from ..utils import format_nums


def embed_play(play_stats: stat_play, client: discord.Client) -> discord.Embed:
    """
    generates status report embed from play

    :param play_stats: user statistics on play
    :param client:discord client of bot
    :return: discord embed with play stats
    """
    desc = ""
    if play_stats.pb:
        desc = f"**__#{play_stats.pb} Top Play!__**"
    embed = discord.Embed(description=desc,
                          url=f"https://osu.ppy.sh/b/{play_stats.beatmap_id}",
                          title=f"{play_stats.map_obj.artist} – {play_stats.map_obj.title} "
                                f"[{play_stats.map_obj.version}]",
                          color=0xbb5577)

    embed.set_author(url=f"https://osu.ppy.sh/u/{play_stats.user_id}",
                     name=f"{play_stats.username} – {play_stats.user_pp:,}pp "
                          f"(#{play_stats.user_rank:,})",
                     icon_url=f"https://a.ppy.sh/{play_stats.user_id}?{int(time())}")

    embed.set_image(url="attachment://strains_bar.png")

    ranked_text = "Submitted"
    approved = play_stats.map_obj.approved
    if approved == 1:
        ranked_text = "Ranked"
    elif approved == 2:
        ranked_text = "Approved"
    elif approved == 3:
        ranked_text = "Qualified"
    elif approved == 4:
        ranked_text = "Loved"

    embed.set_footer(icon_url=f"https://a.ppy.sh/{play_stats.map_obj.creator_id}?{int(time())}",
                     text=f"Mapped by {play_stats.map_obj.creator} {SEPARATOR} {ranked_text} on "
                          f"{play_stats.map_obj.approved_date.format('D MMMM YYYY')}")

    embed.set_thumbnail(url=f"https://b.ppy.sh/thumb/{play_stats.map_obj.beatmapset_id}l.jpg")

    play_results = f"{get_rank_emoji(play_stats.rank, client)} {SEPARATOR} "
    if play_stats.mods:
        play_results += f"+{','.join(sanitize_mods(play_stats.mods))} {SEPARATOR} "

    if play_stats.lb > 0:
        play_results += f"r#{play_stats.lb} {SEPARATOR} "

    play_results += f"{play_stats.score:,} {SEPARATOR} " \
                    f"{format_nums(play_stats.acc, 2)}% {SEPARATOR} " \
                    f"{play_stats.date.humanize()}"

    if play_stats.pp_fc > play_stats.performance_points:
        perfomacne = f"**{'*' if play_stats.unsubmitted else ''}" \
                     f"{format_nums(play_stats.performance_points, 2):,}" \
                     f"pp**{'*' if play_stats.unsubmitted else ''} ➔" \
                     f" {format_nums(play_stats.pp_fc, 2):,}pp for " \
                     f"{format_nums(play_stats.acc_fc, 2)}% FC {SEPARATOR} "
    else:
        perfomacne = f"**{format_nums(play_stats.performance_points, 2):,}pp** {SEPARATOR} "

    if play_stats.combo < play_stats.map_obj.max_combo:
        perfomacne += f"{play_stats.combo:,}/{play_stats.map_obj.max_combo:,}x"
    else:
        perfomacne += f"{play_stats.map_obj.max_combo:,}x"

    if play_stats.pp_fc > play_stats.performance_points:
        perfomacne += "\n"
    elif play_stats.ur or play_stats.count100 or play_stats.count50 or play_stats.countmiss:
        perfomacne += f" {SEPARATOR} "

    if play_stats.count100 > 0:
        perfomacne += f"{play_stats.count100}x100"

    if play_stats.count50 > 0:
        if play_stats.count100 > 0:
            perfomacne += f" {SEPARATOR} "
        perfomacne += f"{play_stats.count50}x50"

    if play_stats.countmiss > 0:
        if play_stats.count100 > 0 or play_stats.count50 > 0:
            perfomacne += f" {SEPARATOR} "
        perfomacne += f"{play_stats.countmiss}xMiss"

    if play_stats.ur is not None and play_stats.ur > 0:
        pass
        # TODO: implrmrnt UR and CV

    if play_stats.completion < 1:
        perfomacne += f"\n**{format_nums(play_stats.completion * 100, 2)}%** completion"

    embed.add_field(name=play_results, value=perfomacne, inline=False)

    beatmap_info = \
        f"{arrow.Arrow(2019, 1, 1).shift(seconds=play_stats.map_obj.total_length).format('mm:ss')}" \
        f" ~ CS**{format_nums(play_stats.map_obj.cs, 1)}** " \
        f"AR**{format_nums(play_stats.map_obj.ar, 1)}** " \
        f"OD**{format_nums(play_stats.map_obj.od, 1)}** " \
        f"HP**{format_nums(play_stats.map_obj.hp, 1)}** ~ "

    if play_stats.map_obj.bpm_min != play_stats.map_obj.bpm_max:
        beatmap_info += f"{format_nums(play_stats.map_obj.bpm_min, 1)}-" \
                        f"{format_nums(play_stats.map_obj.bpm_max, 1)} " \
                        f"(**{format_nums(play_stats.map_obj.bpm, 1)}**) "
    else:
        beatmap_info += f"**{format_nums(play_stats.map_obj.bpm, 1)}** "

    beatmap_info += f"BPM ~ " \
                    f"**{format_nums(play_stats.stars, 2)}**★"

    embed.add_field(name="Beatmap Information", value=beatmap_info, inline=False)

    return embed
