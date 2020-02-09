from utils.config import Users
from utils.discord import help_me, DiscordInteractive
from utils.utils import Log, sanitize

interact = DiscordInteractive.interact


class Command:
    command = "ign-set"
    description = "Sets your username for platform."
    argsRequired = 2
    usage = "[osu|steam] <username>"
    examples = [{
        "run": "set-ign osu nathan on osu",
        "result": "Sets your osu! username to nathan on osu."
    },
        {
            "run": "set steam flyingpigoftheapocalypse",
            "result": "Sets your steam username to flyingpigoftheapocalypse."
        }]
    synonyms = ["set-?ign", "set", "ign", "ignset"]

    async def call(self, package):
        message, args, user_obj = package["message_obj"], package["args"], package["user_obj"]

        try:
            ign = " ".join(args[2:])
            user_id = message.author.id
            platform = f"{sanitize(args[1]).lower()}_ign"
        except IndexError:
            ign = ""
            user_id = message.author.id
            platform = "_ign"

        if len(ign) == 0:
            Log.error("No ign provided")
            await help_me(message, self.command)
            return

        if platform not in user_obj.keys() or platform == "_ign":
            Log.error("Bad platform")
            await help_me(message, self.command)
            return

        Users().set(user_id, platform, ign)

        author = message.author.name
        author = f"{author}'" if author[-1] == "s" else f"{author}'s"

        msg = f"successfully set {author} {args[1]} name set to {ign}"
        Log.log(msg)
        interact(message.channel.send, msg)
