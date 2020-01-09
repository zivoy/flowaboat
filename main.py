import asyncio, aiohttp, html
import generateCommandMD
from utils import sanitize, Log, Config, Users, help_me, Broadcaster
import commands
import administrating
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
import discord
from threading import Thread
from typing import Optional

# Config().load()
# Users().load()


client = discord.Client()
conn = socket(AF_INET, SOCK_DGRAM)
conn.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

commandsLoop: Optional[asyncio.AbstractEventLoop] = None

@client.event
async def on_message(message):
    Log.log(f"{message.author.name}@{message.channel}: {message.content}")

    if message.author == client.user:
        return

    Broadcaster(conn).send(message)

    if message.content.startswith(Config.prefix):
        Users().load()
        Users().add_user(message.author.id)

        mess = message.content.split(" ")
        mess[0] = mess[0][len(Config.prefix):]
        command = mess[0]

        package = {
            "message_obj": message,
            "args": mess,
            "client": client,
            "user_obj": Users.users[str(message.author.id)]
        }

        comm: Optional[commands.templateClass] = None
        if command in commands.List.keys():
            # await getattr(commands, sanitize(command))().call(package)
            comm = getattr(commands, command)()

        else:
            found = False
            for i, j in commands.List.items():
                if any([True for cm in j if cm.search(command)]):
                    # await getattr(commands, sanitize(i))().call(package)
                    comm = getattr(commands, i)()
                    found = True
                    break

            if not found:
                await help_me(message, "help")
                Log.log(f"{command} is not a valid command")

        if comm is not None:
            asyncio.run_coroutine_threadsafe(comm.call(package), commandsLoop)

    elif Config.administer:
        for adm in administrating.List:
            trigBool, payload = adm.trigger(message, client)
            if trigBool:
                await adm.action(message, payload)


def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


@client.event
async def on_ready():
    global commandsLoop
    Log.log('Logged in as')
    Log.log(client.user.name)
    Log.log(client.user.id)
    Log.log('------')
    commandsLoop = asyncio.new_event_loop()
    t = Thread(target=start_background_loop, args=(commandsLoop,), daemon=True)
    t.start()

if __name__ == "__main__":
    client.run(Config.credentials.bot_token)
