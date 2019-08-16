from utils import *
import osu


class Command:
    command = "bpm"
    description = "Plot a graph of the bpm over the course of the song"
    argsRequired = 0
    usage = "[map link] [+mods]"
    examples = [
        {
            "run": "bpm",
            "result": "Returns BPM graph for the last beatmap."
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
                mods = osu.parse_mods_string(i[1:])

        if len(args) > 1 and not args[1].startswith("+"):
            map_link, map_type = osu.get_map_link(args[1])
            Users().set(message.author.id, "last_beatmap",
                        {"map": (map_link, map_type), "mods": mods, "completion": 1, "acc": 1})
        else:
            map_link, map_type = user_data["last_beatmap"]["map"]

        if map_link is None:
            Log.error("No Map provided")
            await help_me(message, "map")
            return

        bpm_graph = osu.graph_bpm(map_link, mods, map_type)

        await message.channel.send(file=bpm_graph.read(), name="BPM Graph.png")
        bpm_graph.close()
