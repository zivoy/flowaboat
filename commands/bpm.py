import discord

from utils.config import Users
from utils.discord import help_me, DiscordInteractive
from utils.osu.graphing import graph_bpm
from utils.osu.stating import MapStats
from utils.osu.utils import get_map_link, parse_mods_string
from utils.utils import Log

interact = DiscordInteractive().interact


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
                mods = parse_mods_string(i[1:])

        if len(args) > 1 and not args[1].startswith("+"):
            map_link, map_type = get_map_link(args[1])
            Users().update_last_message(message.author.id, map_link, map_type, mods, 1, 1, user_data["osu_ign"], None)
        else:
            map_link, map_type = user_data["last_beatmap"]["map"]
            if not mods:
                mods = user_data["last_beatmap"]["mods"]

        if map_link is None:
            Log.error("No Map provided")
            await help_me(message, "map")
            return

        map_obj = MapStats(map_link, mods, map_type)
        bpm_graph = graph_bpm(map_obj)

        Log.log("Posting Graph")
        interact(message.channel.send, file=discord.File(bpm_graph, "BPM_Graph.png"))
        bpm_graph.close()
