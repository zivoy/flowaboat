import discord, asyncio, requests, aiohttp, html, json, random, sys
import commands
from utils import *

Config().load()


client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    print(message.content)
    if message.content.startswith(Config.prefix):
        mess = message.content.split()
        command = mess[0].replace(Config.prefix, "")
        if command in commands.List:
            await getattr(commands, command)(message)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(Config.credentials.bot_token)
