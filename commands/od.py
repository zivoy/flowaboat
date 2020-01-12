from utils.discord import help_me, DiscordInteractive
from utils.osu.utils import CalculateMods
from utils.utils import Log

interact = DiscordInteractive().interact


class Command:
    command = "od"
    description = "Calculate Overall Difficulty values and milliseconds with mods applied."
    argsRequired = 1
    usage = "<od> [+mods]"
    examples = [
        {
            'run': "od 7 +HT",
            'result': "Returns OD of AR8 with HT applied."
        },
        {
            'run': "od 3.5 +HR",
            'result': "Returns OD of AR6.4 with HR applied."
        }]
    synonyms = []

    async def call(self, package):
        message, args = package["message_obj"], package['args']
        try:
            od = float(args[1])
        except ValueError:
            msg = f"{args[1]} is not a valid od"
            # await message.channel.send(msg)
            Log.error(msg)
            await help_me(message, self.command)
            return
        except IndexError:
            Log.error("No od provided")
            await help_me(message, self.command)
            return

        mods = args[2].upper() if len(args) > 2 else ""

        new_od, od_ms, mod_list = CalculateMods(mods).od(od)

        output = ""

        if len(mod_list) > 0:
            if od.is_integer():
                od = int(od)
            output += f"OD{od}+{''.join(mod_list).upper()} -> "

        new_od = float(f"{new_od:.2f}")
        if new_od.is_integer():
            new_od = int(new_od)
        output += f"OD{new_od} ({od_ms:.0f}ms)"

        interact(message.channel.send, output)
