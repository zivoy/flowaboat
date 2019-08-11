import discord, asyncio, requests, aiohttp, html, json, random, sys, re
import commands
from utils import *

Config().load()
Users().load()


client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f"{message.author.name}@{message.channel}: {message.content}")

    if message.content.startswith(Config.prefix):
        if message.author.id not in Users.users:
            Users().add_user(message.author.id)

        mess = message.content.split(" ")
        mess[0] = mess[0][len(Config.prefix):]
        command = ''.join([i for i in mess[0] if not i.isdigit()])

        package = {
            "message_obj": message,
            "args": mess,
            "client": client,
            "user_obj": Users.users[message.author.id]
        }

        if command in commands.List.keys():
            await getattr(commands, command)().call(package)
        else:
            found = False
            for i, j in commands.List.items():
                if command in j:
                    await getattr(commands, i)().call(package)
                    found = True
                    break
            if not found:
                await message.channel.send(f"{command} is not a valid command")
    elif Config.administer:
        pass


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(Config.credentials.bot_token)
