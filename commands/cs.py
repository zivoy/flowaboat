from utils import *
import osuUtils


class Command:
    command = "cs"
    description = "Calculate Circle Size value with mods applied."
    argsRequired = 1
    usage = "<cs> [+mods]"
    examples = [{
        'run': "cs 6 +HR",
        'result': "Returns CS of AR8 with HR applied."
    },
        {
        'run': "cs 8.3 +EZ",
        'result': "Returns CS of AR8.3 with EZ applied."
    }]
    synonyms = []

    async def call(self, package):
        message, args = package["message_obj"], package['args']
        try:
            cs = float(args[1])
        except ValueError:
            msg = f"{args[1]} is not a valid cs"
            # await message.channel.send(msg)
            Log.error(msg)
            await help_me(message, self.command)
            return
        except IndexError:
            Log.error("No cs provided")
            await help_me(message, self.command)
            return

        mods = args[2].upper() if len(args) > 2 else ""

        new_cs, mod_list = osuUtils.CalculateMods(mods).cs(cs)

        output = ""

        if len(mod_list) > 0:
            if cs.is_integer():
                cs = int(cs)
            output += f"CS{cs}+{''.join(mod_list).upper()} -> "

        new_cs = float(f"{new_cs:.2f}")
        if new_cs.is_integer():
            new_cs = int(new_cs)
        output += f"CS{new_cs}"

        await message.channel.send(output)
