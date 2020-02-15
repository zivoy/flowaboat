import discord

from utils import DIGITS
from utils.config import Users
from utils.discord import help_me, DiscordInteractive, get_user
from utils.errors import NoPlays, UserNonexistent
from utils.osu.apiTools import get_top
from utils.osu.embedding import embed_play
from utils.osu.stating import stat_play
from utils.utils import Log

interact = DiscordInteractive.interact


class Command:
    command = "top"
    description = "Show a specific top play."
    argsRequired = 0
    usage = "[username]"
    examples = [
        {
            "run": "top",
            "result": "Returns your #1 top play."
        },
        {
            "run": "top5 vaxei",
            "result": "Returns Vaxei's #5 top play."
        }]
    synonyms = [r"top\d+", r"rb\d+", r"recentbest\d+", r"ob\d+", r"oldbest\d+"]

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

        rb = True if any([i in args[0] for i in ["rb", "recentbest"]]) else False
        ob = True if any([i in args[0] for i in ["ob", "oldbest"]]) else False

        if index is None:
            index = 1
        else:
            index = int(index.group(1))

        try:
            top_play = get_top(user, index, rb, ob)
        except NoPlays as err:
            interact(message.channel.send, err)
            return

        try:
            play_data = stat_play(top_play)
        except Exception as err:
            interact(message.channel.send, err)
            Log.error(err)
            return

        Users().update_last_message(message.author.id, top_play.beatmap_id, "id",
                                    top_play.enabled_mods, 1, top_play.accuracy, user, play_data.replay)

        embed = embed_play(play_data, client)
        graph = discord.File(play_data.strain_bar, "strains_bar.png")

        interact(message.channel.send, file=graph, embed=embed)
        Log.log(f"Returning top play #{play_data.pb} for {user}")
