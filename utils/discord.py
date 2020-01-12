import asyncio
import json

import discord

import commands
from .config import Config, Users
from .errors import UserNonexistent
from .utils import Dict, sanitize, Log


class Broadcaster:
    def __init__(self, connection_socket):
        self.socket = connection_socket

    def send(self, message, port=12345):
        guild = Dict({"id": None, "name": None}) if message.guild is None else message.guild
        channel = Dict({"id": message.channel.id, "name": "DM"}) \
            if isinstance(message.channel, discord.DMChannel) else message.channel
        package = {"sender":
            {
                "id": message.author.id,
                "name": message.author.name
            },
            "content": message.content,
            "message_id": message.id,
            "guild":
                {
                    "name": guild.name,
                    "id": guild.id
                },
            "channel":
                {
                    "name": channel.name,
                    "id": channel.id
                }
        }
        self.socket.sendto(json.dumps(package).encode(), ('255.255.255.255', port))

    def receive(self, bytes_to_receive=1024):
        rawMessage = self.socket.recvfrom(bytes_to_receive)[0]
        return Dict(json.loads(rawMessage.decode()))

    @staticmethod
    def is_by_author(original, new):
        guild = None if original.guild is None else original.guild.id
        channel = original.channel.id
        name = original.author.id
        return new["guild"]["id"] == guild and channel == new["channel"]["id"] and new["sender"]["id"] == name


class DiscordInteractive:
    """
    run a command on the main async loop
    useful for discord interaction channel
    """
    loop = None

    def interact(self, command, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self.__executor(command, *args, **kwargs), self.loop)
        return future.result(600)

    @staticmethod
    async def __executor(command, *args, **kwargs):
        return await command(*args, **kwargs)


def command_help(command):
    """
    formats a discord embed for information on a command

    :param command: command to get info on
    :return: discord embed
    """
    for i, j in commands.List.items():
        if command == i or any([True for cm in j if cm.search(command)]):
            command = getattr(commands, sanitize(i))()
            command_text = f"{Config.prefix}{i}"

            help_page = discord.Embed(title="Command",
                                      description=f"`{command_text}`")

            if command.synonyms:
                help_page.add_field(name="Synonyms",
                                    value=", ".join([f"`{Config.prefix}{i}`"
                                                     for i in command.synonyms]), inline=False)

            help_page.add_field(name="Description", value=command.description, inline=False)

            help_page.add_field(name="Usage", value=f"**Required variables**: "
                                                    f"`{command.argsRequired}`\n"
                                                    f"```{command_text} {command.usage}```",
                                inline=False)

            examples = command.examples
            emps = "s" if len(examples) > 1 else ""
            examps = "\n\n".join([f"```{Config.prefix}"
                                  f"{i['run']}```{i['result']}" for i in examples])
            help_page.add_field(name="Example" + emps, value=examps, inline=False)

            Log.log("Retuning help page for", command_text)
            return help_page

    Log.error(command, "is not a not valid command")
    return discord.Embed(title="ERROR", description="Command not found")


async def help_me(message_obj, command):
    """
    get help on command and post embed

    :param message_obj: a discord message object
    :param command: command to get help on
    """
    await getattr(commands, "help")().call({"message_obj": message_obj, "args": ["", command]})


def fetch_emote(emote_name, guild, client):
    """
    find an emote from its name in all servers the bot is part of

    :param emote_name: the name of the emote
    :param guild: a specific guild to search
    :param client: discord client object
    :return: discord emote
    """
    e_lists = []
    if guild:
        e_lists.extend(guild.emojis)
    e_lists.extend(client.emojis)
    valid = [x for x in e_lists if x.name.lower() == emote_name.lower()]
    if not valid:
        Log.error("Not valid emote")
        return False
    return valid[0]


def get_user(args, ign, platfrom):
    """
    extracts the users ign from input list or from the value provided

    :param args: the input list
    :param ign: the name if known
    :param platfrom: from what platfrom is the ign osu|steam
    :return: ign
    """
    name = " ".join(args[1:])

    if ign and not name:
        return ign

    if (name.startswith("<@") or name.startswith("<@!")) and name.endswith(">"):
        uid = name[2:-1]
        if not uid.isnumeric():
            uid = name[3:-1]
        if uid in Users.users.keys():
            try:
                return Users.users[uid][platfrom + "_ign"]
            except IndexError:
                raise UserNonexistent

    return name
