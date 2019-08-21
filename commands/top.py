from utils import *
import osuUtils


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
    synonyms = [r"top\d+", "rb", "recentbest", "ob", "oldbest"]

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
            await message.channel.send("User does not exist")
            return

        index = digits.match(args[0])

        rb = True if args[0] == "rb" or args[0] == "recentbest" else False
        ob = True if args[0] == "ob" or args[0] == "oldbest" else False

        if index is None:
            index = 1
        else:
            index = int(index.captures(1)[0])

        try:
            top_play = osuUtils.get_top(user, index, rb, ob)
        except osuUtils.NoPlays as err:
            await message.channel.send(err)
            return

        Users().update_last_message(message.author.id, top_play.beatmap_id, "id",
                                    top_play.enabled_mods, 1, top_play.accuracy)

        try:
            play_data = osuUtils.stat_play(top_play)
        except Exception as err:
            await message.channel.send(err)
            Log.error(err)
            return

        embed = osuUtils.embed_play(play_data, client)
        graph = discord.File(play_data.strain_bar, "strains_bar.png")

        await message.channel.send(file=graph, embed=embed)
        Log.log(f"Returning top play {index} for {user}")