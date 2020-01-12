import discord

from utils import DIGITS
from utils.config import Users
from utils.discord import help_me, get_user, DiscordInteractive
from utils.errors import UserNonexistent, NoPlays
from utils.osu.apiTools import get_recent
from utils.osu.embedding import embed_play
from utils.osu.stating import stat_play
from utils.utils import Log

interact = DiscordInteractive().interact


class Command:
    command = "recent"
    description = "Show recent score or pass."
    argsRequired = 0
    usage = "[username]"
    examples = [
        {
            "run": "recent nathan_on_osu",
            "result": "Returns nathan on osu's most recent score."
        },
        {
            "run": "recent3 respektive",
            "result": "Returns respektive's most recent score."
        },
        {
            "run": "recentpass",
            "result": "Returns your most recent pass."
        }]
    synonyms = [r"recent\d+", "rs", "recentpass", "rp"]

    async def call(self, package):
        message, args, user_data, client = package["message_obj"], package["args"], \
                                           package["user_obj"], package["client"]

        if len(args) < 2 and user_data["osu_ign"] == "":
            Log.error("No User provided")
            await help_me(message, "ign-set")
            return

        try:
            user = get_user(args, user_data["osu_ign"], "osu")
        except UserNonexistent:
            interact(message.channel.send, "User does not exist")
            return

        index = DIGITS.match(args[0])

        if index is None:
            index = 1
        else:
            index = int(index.captures(1)[0])

        try:
            recent_play = get_recent(user, index)
        except NoPlays as err:
            interact(message.channel.send, f"`{err}`")
            Log.log(err)
            return

        try:
            play_data = stat_play(recent_play)
        except Exception as err:
            interact(message.channel.send, err)
            Log.error(err)
            return

        Users().update_last_message(message.author.id, recent_play.beatmap_id, "id",
                                    recent_play.enabled_mods, play_data.completion, recent_play.accuracy, user,
                                    play_data.replay)

        embed = embed_play(play_data, client)
        graph = discord.File(play_data.strain_bar, "strains_bar.png")

        interact(message.channel.send, file=graph, embed=embed)
        Log.log(f"Returning recent play #{index} for {user}")
