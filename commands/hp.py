from utils import *
import osuUtils


class Command:
    command = "hp"
    description = "Calculate Health value with mods applied."
    argsRequired = 1
    usage = "<hp> [+mods]"
    examples = [{
        'run': "hp 4 +HR",
        'result': "Returns HP of AR8 with HR applied."
    },
        {
        'run': "hp 7 +EZ",
        'result': "Returns HP of AR6.4 with EZ applied."
    }]
    synonyms = []

    async def call(self, package):
        message, args = package["message_obj"], package['args']
        try:
            hp = float(args[1])
        except ValueError:
            msg = f"{args[1]} is not a valid hp"
            # await message.channel.send(msg)
            Log.error(msg)
            await help_me(message, self.command)
            return
        except IndexError:
            Log.error("No ar provided")
            await help_me(message, self.command)
            return

        mods = args[2].upper() if len(args) > 2 else ""

        new_hp, mod_list = osuUtils.CalculateMods(mods).hp(hp)

        output = ""

        if len(mod_list) > 0:
            if hp.is_integer():
                hp = int(hp)
            output += f"HP{hp}+{''.join(mod_list).upper()} -> "

        new_hp = float(f"{new_hp:.2f}")
        if new_hp.is_integer():
            new_hp = int(new_hp)
        output += f"HP{new_hp}"

        await message.channel.send(output)
