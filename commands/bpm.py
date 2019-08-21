from utils import *
import osuUtils


class Command:
    command = "bpm"
    description = "Plot a graph of the bpm over the course of the song"
    argsRequired = 0
    usage = "[map link] [+mods]"
    examples = [
        {
            "run": "bpm +DT",
            "result": "Returns BPM graph for the last beatmap with Double time."
        },
        {
            "run": "bpm https://osu.ppy.sh/beatmapsets/545156#osu/1262906",
            "result": f"Returns a BPM chart for Loose Change [Rohit's Insane]."
        }]
    synonyms = []

    async def call(self, package):
        message, args, user_data = package["message_obj"], package["args"], package["user_obj"]

        mods = []
        for i in args:
            if i.startswith("+"):
                mods = osuUtils.parse_mods_string(i[1:])

        if len(args) > 1 and not args[1].startswith("+"):
            map_link, map_type = osuUtils.get_map_link(args[1])
            Users().update_last_message(message.author.id, map_link, map_type, mods, 1, 1)
        else:
            map_link, map_type = user_data["last_beatmap"]["map"]
            if not mods:
                mods = user_data["last_beatmap"]["mods"]

        if map_link is None:
            Log.error("No Map provided")
            await help_me(message, "map")
            return

        bpm_graph = osuUtils.graph_bpm(map_link, mods, map_type)

        Log.log("Posting Graph")
        await message.channel.send(file=discord.File(bpm_graph, "BPM_Graph.png"))
        bpm_graph.close()
