from utils import *


class Command:
    command = "help"
    description = "Get help for a command. \n\n **List of all commands**: \n " \
                  "https://github.com/zivoy/flowaboat/blob/pythonized/COMMANDS.md"
    argsRequired = 1
    usage = "<command>"
    examples = [{
        "run": "help pp",
        "result": f"Returns help on how to use the `{Config.prefix}pp` command."
    }]
    synonyms = ["h"]

    async def call(self, package):
        message, args = package["message_obj"], package["args"]

        try:
            embed = command_help(args[1])
        except IndexError:
            Log.error("No command provided")
            await help_me(message, self.command)
            return

        await message.channel.send(embed=embed)
