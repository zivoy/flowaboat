class hello:
    command = "hello"
    description = "say hello back"
    argsRequired = 0
    usage = "hello"
    example = {
        'run': "hello",
        'result': "hello <@user>"
    }
    synonyms = ["hi"]

    async def call(self, message):
        msg = 'Hello {0.author.mention}'.format(message)
        await message.channel.send(msg)
