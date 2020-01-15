import asyncio
import json

import discord

import commands
from .config import Config, Users
from .errors import UserNonexistent
from .utils import Dict, sanitize, Log, validate_date
import requests
import regex
from io import BytesIO


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
        if isinstance(original, discord.Message):
            guild = None if original.guild is None else original.guild.id
            channel = original.channel.id
            name = original.author.id
        else:
            guild= original["guild"]["id"]
            channel = original["channel"]["id"]
            name = original["sender"]["id"]
        return new["guild"]["id"] == guild and channel == new["channel"]["id"] and new["sender"]["id"] == name


class DiscordInteractive:
    """
    run a command on the main async loop
    useful for discord interaction channel
    """
    loop = None

    @classmethod
    def interact(cls, command, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(cls.__executor(command, *args, **kwargs), cls.loop)
        return future.result(600)

    @staticmethod
    async def __executor(command, *args, **kwargs):
        return await command(*args, **kwargs)


class Question:
    def __init__(self, listener, original_message, sender):
        self.original = original_message
        self.sender = sender
        self.listener = listener

    @staticmethod
    def stop_check(user_input):
        return user_input["content"].lower() in ["cancel", "stop"]

    async def _delete_messages(self, messages):
        for i in messages:
            mess = await self.original.channel.fetch_message(i)
            await mess.delete()

    def delete_messages(self, messages):
        DiscordInteractive.interact(self._delete_messages, messages)
        for i, _ in enumerate(messages):
            del messages[i]

    def multiple_choice(self, question, option_list):
        options = question+"\n>>> "
        options += "\n".join([f"`{i+1}` {j}" for i, j in enumerate(option_list)])
        messages = list()

        DiscordInteractive.interact(self.original.edit, content=options)
        while True:
            uInput = self.listener.receive()
            if Broadcaster.is_by_author(self.sender, uInput):
                # Log.log("input is", uInput)
                messages.append(uInput["message_id"])
                DiscordInteractive.interact(self.original.edit, embed=None)
                if uInput["content"].isnumeric():
                    num = int(uInput["content"])
                    if 1 <= num <= len(option_list)+1:
                        self.delete_messages(messages)
                        DiscordInteractive.interact(self.original.edit, embed=None)
                        return num - 1
                    else:
                        badin = discord.Embed(title="BAD INPUT",
                                              description=f"Please choose between `1` and `{len(option_list)+1}`")
                        DiscordInteractive.interact(self.original.edit, embed=badin)
                        continue
                elif self.stop_check(uInput):
                    self.delete_messages(messages)
                    return False
                else:
                    badin = discord.Embed(title="BAD INPUT",
                                          description="Please choose an integer")
                    DiscordInteractive.interact(self.original.edit, embed=badin)
                    continue

    def get_real_number(self, question, is_integer=False, is_positive=False, minimum=None, maximum=None):
        messages = list()

        DiscordInteractive.interact(self.original.edit, content=question)
        while True:
            uInput = self.listener.receive()
            if Broadcaster.is_by_author(self.sender, uInput):
                # Log.log("input is", uInput)
                messages.append(uInput["message_id"])
                DiscordInteractive.interact(self.original.edit, embed=None)
                if uInput["content"].replace(".", "", 1).replace("-", "", 1).replace("+", "", 1).isnumeric():
                    num = float(uInput["content"])

                    if is_integer and not num.is_integer():
                        badin = discord.Embed(title="BAD INPUT", description="Please choose an integer")
                        DiscordInteractive.interact(self.original.edit, embed=badin)
                        continue
                    if is_positive and not num > 0:
                        badin = discord.Embed(title="BAD INPUT", description="Please choose a positive number")
                        DiscordInteractive.interact(self.original.edit, embed=badin)
                        continue
                    if minimum is not None and num < minimum:
                        badin = discord.Embed(title="OUT OF BOUNDS", description=f"The minimum number is {minimum}")
                        DiscordInteractive.interact(self.original.edit, embed=badin)
                        continue
                    if maximum is not None and maximum <= num:
                        badin = discord.Embed(title="OUT OF BOUNDS", description=f"The maximum number is {maximum}")
                        DiscordInteractive.interact(self.original.edit, embed=badin)
                        continue

                    self.delete_messages(messages)
                    DiscordInteractive.interact(self.original.edit, embed=None)
                    return num
                elif self.stop_check(uInput):
                    self.delete_messages(messages)
                    return False
                else:
                    badin = discord.Embed(title="BAD INPUT", description="Please choose a number")
                    DiscordInteractive.interact(self.original.edit, embed=badin)
                    continue

    def get_string(self, question, confirm=False):
        messages = list()

        DiscordInteractive.interact(self.original.edit, content=question)
        while True:
            uInput = self.listener.receive()
            if Broadcaster.is_by_author(self.sender, uInput):
                # Log.log("input is", uInput)
                messages.append(uInput["message_id"])
                message = uInput["content"]

                if self.stop_check(uInput):
                    self.delete_messages(messages)
                    return False

                if confirm:
                    self.delete_messages(messages)
                    con = self.multiple_choice(
                        f"Your message is \n```\n{message}\n```\nDo you confirm?", ["Yes", "No"])
                    if isinstance(con, bool) and not con:
                        self.delete_messages(messages)
                        return False
                    if con == 0:
                        return message
                    else:
                        DiscordInteractive.interact(self.original.edit, content=question)
                        continue

                self.delete_messages(messages)
                DiscordInteractive.interact(self.original.edit, embed=None)
                return message

    def get_date(self, question, required=True, tzinfo=None):
        image = requests.get("http://c.tadst.com/gfx/tzmap/map.1578751200.png", allow_redirects=True).content
        map_file = discord.File(BytesIO(image), "timezonemap.png")
        date_form = regex.compile(r"^(?:\d\d\d\d)([- \/.])(?:0?[1-9]|1[012])\1(?:0[1-9]|[12][0-9]|3[01])$")

        if not required:
            sub = self.multiple_choice(question+"\n\n This is not required", ["Submit a date", "Leave blank"])
            if sub:
                return None, tzinfo

        if tzinfo is None:
            DiscordInteractive.interact(self.original.edit, embed=None)
            mep = DiscordInteractive.interact(self.original.channel.send, file=map_file)
            tzinfo = self.get_real_number("What is your time zone?\npick from the image", True, False, -11, 12)
            if isinstance(tzinfo, bool) and not tzinfo:
                return False
            tzinfo = -tzinfo
            DiscordInteractive.interact(mep.delete)

        while True:
            date_str = self.get_string(question+"\n\nInput the date in the format:\n> year/month/day")
            if isinstance(date_str, bool) and not date_str:
                return False, None
            badin = discord.Embed(title="BAD DATE", description="Input should be like 2015/04/16")
            if date_form.search(date_str):
                seperator = date_form.search(date_str).groups(1)[0]
                date_frms = ["YYYY{0}M{0}D",
                             "YYYY{0}M{0}DD",
                             "YYYY{0}MM{0}D",
                             "YYYY{0}MM{0}DD"]
                for i in date_frms:
                    date_frm = i.format(seperator)
                    date = validate_date(date_str, date_frm, tzinfo=f"gmt{tzinfo}")
                    if date:
                        break
                else:
                    DiscordInteractive.interact(self.original.edit, embed=badin)
                    continue
                break
            else:
                DiscordInteractive.interact(self.original.edit, embed=badin)
                continue

        while True:
            DiscordInteractive.interact(self.original.edit, embed=None)
            time_str = self.get_string(question + "\n\nInput the time in 24 hour format:\n> hours:minuets")
            if isinstance(time_str, bool) and not time_str:
                return False, None
            time = regex.search(r"^([01]?\d|2[0-3]):([0-5]\d)$", time_str)
            if time:
                date = date.shift(hours=int(time.group(1)[0]), minutes=int(time.groups(2)[0]))
                break
            else:
                badin = discord.Embed(title="BAD TIME", description="Input should be like 13:30")
                DiscordInteractive.interact(self.original.edit, embed=badin)
                continue

        DiscordInteractive.interact(self.original.edit, embed=None)
        return date, tzinfo


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
