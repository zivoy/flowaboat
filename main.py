import discord, asyncio, requests, aiohttp, html, json, random, sys
import commands
from utils import *

Config().load()


client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f"{message.author.name}@{message.channel}: {message.content}")

    if message.content.startswith(Config.prefix):
        mess = message.content.split()
        command = mess[0].replace(Config.prefix, "")
        command = ''.join([i for i in command if not i.isdigit()])

        if command in commands.List.keys():
            await getattr(commands, command).call(command, message)
        else:
            found = False
            for i, j in commands.List.items():
                if command in j:
                    await getattr(commands, i).call(command, message)
                    found = True
                    break
            if not found:
                await message.channel.send(f"{command} is not a valid command")


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(Config.credentials.bot_token)
