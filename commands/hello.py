async def hello(message):
    msg = 'Hello {0.author.mention}'.format(message)
    await message.channel.send(msg)
