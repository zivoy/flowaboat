from utils import *


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
        await message.channel.send(msg)
