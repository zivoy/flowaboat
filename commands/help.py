from utils import *

class Command:
    command = "help"
    description = "Get help for a command. __to come__ \n\n \
                    **List of all commands:** https://github.com/zivoy/flowaboat/blob/master/COMMANDS.md"
    argsRequired = 1
    usage = "<command>"
    examples = [{
        "run": "help pp",
        "result": f"Returns help on how to use the `{Config.prefix}pp` command."
    }]
    synonyms = ["h"]

    async def call(self, package):
        message, args = package["message_obj"], package["args"]

        await message.channel.send(embed=command_help(args[1]))
