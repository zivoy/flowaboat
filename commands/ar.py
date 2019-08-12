from utils import *
import osu

class hello:
    command = "ar"
    description = "Calculate Approach Rate values and miliseconds with mods applied."
    argsRequired = 1
    usage = "<ar> [+mods]"
    example = {
        'run': "ar 8 +DT",
        'result': "Returns AR of AR8 with DT applied."
    }
    synonyms = []

    async def call(self, package):
        message, args = package["message_obj"], package['args']
        try:
            ar = float(args[1])
        except ValueError:
            msg = f"{args[1]} is not a valid ar"
            await message.channel.send(msg)
            Log.error(msg)
            return

        mods = args[2].upper() if len(args) > 2 else ""
        osu.calculate_ar(ar, mods)
