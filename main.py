import discord, asyncio, requests, aiohttp, html, json, random, sys
from discord.ext import commands
from utils import *

config = Config().load().config

config.credentials.bot_token = 'NDc4MTE5ODg5MzgzNzE4OTEz.XU824g.o7ub_Xz64ffSsTtaOdSjh8gKh_g'  # test token

bot = commands.Bot(command_prefix=commands.when_mentioned_or(config.prefix))


client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    print(message.content)
    if message.content.startswith(f'{config.prefix}hello'):
        msg = 'Hello {0.author.mention}'.format(message)
        await message.channel.send(msg)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(config.credentials.bot_token)
