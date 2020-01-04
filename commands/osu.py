from time import time

import osu_utils
from utils import Log, SEPARATOR, UserNonexistent, get_user, help_me
import discord


class Command:
    command = "osu"
    description = "Show osu! stats."
    argsRequired = 0
    usage = "[username]"
    examples = [{
        "run": "osu",
        "result": "Returns your osu! stats."
    },
        {
        'run': "osu nathan_on_osu",
        'result': "Returns nathan on osu's osu! stats."
    }]
    synonyms = []

    async def call(self, package):
        message, args, user_data, client = package["message_obj"], package["args"], \
                                           package["user_obj"], package["client"]

        if len(args) < 2 and user_data["osu_ign"] == "":
            Log.error("No User provided provided")
            await help_me(message, "ign-set")
            return

        try:
            user = get_user(args, user_data["osu_ign"], "osu")
        except UserNonexistent:
            await message.channel.send("User does not exist")
            return

        try:
            user_profile = osu_utils.get_user(user)
        except UserNonexistent as err:
            await message.channel.send(err)
            return

        profile = user_profile[0]

        grades = \
            f"{osu_utils.get_rank_emoji('XH', client)} {int(profile['count_rank_ssh']):,} " \
            f"{osu_utils.get_rank_emoji('X', client)} {int(profile['count_rank_ss']):,} " \
            f"{osu_utils.get_rank_emoji('SH', client)} {int(profile['count_rank_sh']):,} " \
            f"{osu_utils.get_rank_emoji('S', client)} {int(profile['count_rank_s']):,} " \
            f"{osu_utils.get_rank_emoji('A', client)} {int(profile['count_rank_a']):,}"

        seconds = int(profile['total_seconds_played'])
        play_time = f"{round(seconds / 3600)}h {round(seconds % 3600 / 60)}m"

        embed = discord.Embed().from_dict(
            {
                "color": 0xbb5577,
                "thumbnail": {
                    "url": f"https://a.ppy.sh/{profile['user_id']}?{int(time())}"
                },
                "author": {
                    "name": f"{profile['username']} – {float(profile['pp_raw']):,.2f}pp (#{int(profile['pp_rank']):,}) "
                    f"({profile['country']}#{int(profile['pp_country_rank']):,})",
                    "icon_url": f"https://a.ppy.sh/{profile['user_id']}?{int(time())}",
                    "url": f"https://osu.ppy.sh/u/{profile['user_id']}"
                },
                "footer": {
                    "text": f"Playing for {profile['join_date'].humanize(only_distance=True)} "
                    f"{SEPARATOR} Joined on {profile['join_date'].format('D MMMM YYYY')}"
                },
                "fields": [
                    {
                        "name": 'Ranked Score',
                        "value": f"{int(profile['ranked_score']):,}",
                        "inline": True
                    },
                    {
                        "name": 'Total score',
                        "value": f"{int(profile['total_score']):,}",
                        "inline": True
                    },
                    {
                        "name": 'Play Count',
                        "value": f"{int(profile['playcount']):,}",
                        "inline": True
                    },
                    {
                        "name": 'Play Time',
                        "value": play_time,
                        "inline": True
                    },
                    {
                        "name": 'Level',
                        "value": f"{float(profile['level']):.2f}",
                        "inline": True
                    },
                    {
                        "name": 'Hit Accuracy',
                        "value": f"{float(profile['accuracy']):.2f}%",
                        "inline": True
                    },
                    {
                        "name": 'Grades',
                        "value": grades
                    }
                ]
            })

        await message.channel.send(embed=embed)
