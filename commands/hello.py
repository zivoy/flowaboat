from utils.discord import DiscordInteractive
from utils.utils import Log

interact = DiscordInteractive.interact


class Command:
    command = "hello"
    description = "say hello back"
    argsRequired = 0
    usage = ""
    examples = [{
        'run': "hello",
        'result': "hello <@user>"
    }]
    synonyms = ["hi"]

    async def call(self, package):
        message = package["message_obj"]
        msg = 'Hello {0.author.mention}'.format(message)
        Log.log(msg)
        interact(message.channel.send, msg)
