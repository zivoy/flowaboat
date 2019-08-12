from utils import *
import osu


class Command:
    command = "ar"
    description = "Calculate Approach Rate values and milliseconds with mods applied."
    argsRequired = 1
    usage = "<ar> [+mods]"
    examples = [{
        'run': "ar 8 +DT",
        'result': "Returns AR of AR8 with DT applied."
    },
        {
        'run': "ar 6.4 +EZ",
        'result': "Returns AR of AR6.4 with EZ applied."
    }]
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

        new_ar, ar_ms, mod_list = osu.calculate_ar(ar, mods)

        output = ""

        if len(mod_list) > 0:
            if ar.is_integer():
                ar = int(ar)
            output += f"AR{ar}+{''.join(mod_list).upper()} -> "

        new_ar = float(f"{new_ar:.2f}")
        if new_ar.is_integer():
            new_ar = int(new_ar)
        output += f"AR{new_ar} ({ar_ms:.0f}ms)"

        await message.channel.send(output)
