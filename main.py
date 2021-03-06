import asyncio
# aiohttp, html  # these might be needed
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
from threading import Thread
from typing import Optional

import discord

from utils.config import Config, Users
from utils.utils import sanitize, Log

import commands
import administrating
import generateCommandMD
from utils.discord import Broadcaster, DiscordInteractive
from utils.discord import help_me
import utils.discord as util_discord

# Config().load()
# Users().load()

generateCommandMD.generate()

client = discord.Client()
conn = socket(AF_INET, SOCK_DGRAM)
conn.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

commandsLoop: Optional[asyncio.AbstractEventLoop] = None


@client.event
async def on_message(message):
    Log.log(f"{message.author.name}@{message.channel}: {message.content}")
    if DiscordInteractive.client != client:
        DiscordInteractive.client = client
    if DiscordInteractive.loop != asyncio.get_event_loop():
        DiscordInteractive.loop = asyncio.get_event_loop()
    if message.author == client.user:
        return

    Broadcaster(conn).send(message)

    if message.content.startswith(Config.prefix):
        Users().load()
        Users().add_user(message.author.id)

        mess = message.content[len(Config.prefix):]
        mess = mess.split(" ")
        command = mess[0]

        package = {
            "message_obj": message,
            "args": mess,
            "client": client,
            "user_obj": Users.users[str(message.author.id)]
        }

        comm: Optional[commands.templateClass] = None
        if command in commands.List.keys():
            comm = getattr(commands, sanitize(command))()

        else:
            found = False
            for i, j in commands.List.items():
                if any([True for cm in j if cm.search(command)]):
                    comm = getattr(commands, sanitize(i))()
                    found = True
                    break

            if not found:
                comm = getattr(commands, "help")()
                Log.log(f"{command} is not a valid command")  # todo change to show list of available commands

        if comm is not None:
            asyncio.run_coroutine_threadsafe(comm.call(package), commandsLoop)

    elif Config.administer:
        for adm in administrating.List:
            trig_bool, payload = adm.trigger(message, client, commandsLoop)
            if trig_bool:
                await adm.action(message, payload)


def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


workerThread: Optional[Thread] = None


@client.event
async def on_ready():
    global commandsLoop, workerThread
    Log.log('Logged in as')
    Log.log(client.user.name)
    Log.log(client.user.id)
    Log.log('------')
    DiscordInteractive.client = client
    DiscordInteractive.loop = asyncio.get_event_loop()  # message loop
    commandsLoop = asyncio.new_event_loop()
    workerThread = Thread(target=start_background_loop, args=(commandsLoop,), daemon=True)
    workerThread.start()


@client.event
async def on_disconnect():
    global workerThread
    Log.error("disconnected")
    if workerThread is not None and workerThread.is_alive():
        workerThread = None


if __name__ == "__main__":
    client.run(Config.credentials.bot_token)
