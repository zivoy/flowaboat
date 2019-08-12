from utils import *

class Command:
    command = "ign-set"
    description = "Sets your username for platform."
    argsRequired = 2
    usage = "[osu|steam] <username>"
    example = {
        "run": "ign-set osu nathan on osu",
        "result": "Sets your osu! username to nathan on osu."
    }
    synonyms = ["set-ign", "set"]

    async def call(self, package):
        message, args, user_obj = package["message_obj"], package["args"], package["user_obj"]

        ign = "".join(args[2:])
        user_id = message.author.id
        platform = f"{sanitize(args[1]).lower()}_ign"

        if len(ign) == 0:
            Log.error("No ign provided")
            return

        if platform not in user_obj.keys() or platform == "_ign":
            Log.error("Bad platform")
            return

        Users().set(user_id, platform, ign)

        author = message.author.name
        author = f"{author}'" if author[-1] == "s" else f"{author}'s"

        msg = f"successfully set {author} {args[1]} name set to {ign}"
        Log.log(msg)
        await message.channel.send(msg)
