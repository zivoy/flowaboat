"""
all functions and utility's for flowaboat
"""

import json
import os
from time import sleep

import arrow
import discord
import regex
import requests
import socket
from typing import Union, Optional
import asyncio

import commands


class UserError(Exception):
    """
    class used to handel general user errors
    """


class UserNonexistent(UserError):
    """
    error for nonexistent user
    """


class Api:
    def __init__(self, base_url: str, max_requests_per_minute: int = 60, params: dict = None):
        """
        expansion on the requests api that allows to limit requests and store base url as object

        :param params: any default parameters (a.e api key)
        :param base_url: base url that requests expand on
        :param max_requests_per_minute: maximum number of requests per minute
        """
        if params is None:
            params = dict()
        self.url = base_url
        self.params = params
        self.max_requests = max_requests_per_minute
        self.actions = list()

    def clear_queue(self):
        """
        clears queue
        """
        for i in self.actions.copy():
            if (arrow.utcnow() - i).seconds >= 60:
                self.actions.pop(0)
            else:
                break

    def get(self, url, params=None, **kwargs):
        """
        make get requests to api

        :param url: expands on base url
        :param params: parameter dictionary
        :return: requests response
        """
        self.clear_queue()

        if len(self.actions) <= self.max_requests:
            url = self.url + url
            if params is not None:
                for k, j in self.params.items():
                    params[k] = j
            elif self.params != {}:
                params = self.params
            self.actions.append(arrow.utcnow())
            return requests.get(url, params, **kwargs)

        sleep(max(60.1 - (arrow.utcnow() - self.actions[0]).seconds, 0))
        return self.get(url, params, **kwargs)


class JasonFile:
    """
    class for handling the importing and exporting json files to classes
    """
    file = ""

    def open_dir(self, obj, skip=None, itms=None):
        """
        get values out of class and make it a dict

        :param obj: class object
        :param skip: values to skip
        :param itms: expand on a dict
        """
        if itms is None:
            itms = dict()
        if skip is None:
            skip = list()
        for i in dir(self):
            if i in skip:
                pass
            elif not callable(getattr(obj, i)) and not i.startswith("__"):
                itms[i] = getattr(obj, i)
            elif isinstance(getattr(obj, i), type) and not i.startswith("__"):
                itms[i] = dict()
                self.open_dir(getattr(obj, i), skip, itms[i])
        return itms

    def close_dir(self, obj, info):
        """
        but all values into class from dict

        :param obj: class object
        :param info: dict
        """
        for i, j in info.items():
            if not isinstance(getattr(obj, i), type):
                setattr(obj, i, j)
            else:
                self.close_dir(getattr(obj, i), info[i])

    def load(self):
        """
        reads all values from json file into object class
        """
        if not os.path.isfile(self.file):
            # os.mknod(self.file)
            open(self.file, "w").close()
            self.save()
        with open(self.file, "r") as configs:
            self.close_dir(self.__class__, json.load(configs))

    def save(self):
        """
        saves object class into json file
        """
        with open(self.file, "w") as outfile:
            json.dump(self.open_dir(self.__class__, ["file"]), outfile, indent="  ", sort_keys=True)


# todo: make for multi server compatibility
class Config(JasonFile):
    """
    stores server settings
    """
    file = "config.json"

    prefix: str = ""
    debug: bool = False
    administer: bool = False
    osu_cache_path: str = ""
    pp_path: str = ""

    class credentials:
        bot_token: str = ""
        discord_client_id: str = ""
        osu_api_key: str = ""
        twitch_client_id: str = ""
        pexels_key: str = ""
        last_fm_key: str = ""

    class logsCredentials:
        rawPassword: str = ""
        encPassword: str = ""


# todo: have each user be its separate file // maybe also pickling
class Users(JasonFile):
    """
    stores some information on users
    """
    file = "users.list"

    users = dict()

    def add_user(self, uuid: str, osu_ign: str = "", steam_ign: str = ""):
        """
        add new user
        :param uuid: discord id
        :param osu_ign: osu name
        :param steam_ign: steam name
        """
        uuid = str(uuid)
        if uuid not in self.users:
            self.users[uuid] = {"osu_ign": osu_ign, "steam_ign": steam_ign,
                                "last_beatmap": {"map": (None, ""), "mods": [],
                                                 "completion": 0, "accuracy": 0,
                                                 "user": osu_ign, "replay": None},
                                "last_message": None}
            self.save()

    def set(self, uuid: str, item, value):
        """
        updates user data
        :param uuid: discord id
        :param item: item to change
        :param value: value to be set to
        """
        self.users[str(uuid)][item] = value
        self.save()

    def update_last_message(self, user: Union[str,int], map_link, map_type: str, mods: list,
                            completion: float, accuracy: float, user_ign: str, replay):
        """
        updates last message sent by user
        :param user: user id
        :param map_link: any linking data to map correspond with appropriate type
        :param map_type: id|map|path|url
        :param mods: mods used
        :param completion: % completion
        :param accuracy: acc on map
        :param user_ign: users osu ign
        :param replay: encoded replay string (if available)
        """
        self.set(user, "last_beatmap",
                 {"map": (map_link, map_type), "mods": mods,
                  "completion": completion, "accuracy": accuracy,
                  "user": user_ign, "replay": replay})


#


Config().load()
Users().load()


#


# todo: implement livelogs
class Log:
    """
    logging functions
    """

    @staticmethod
    def log(*args):
        """
        log

        :param args: anything that has to be logged
        """
        msg = f"{arrow.utcnow().isoformat()}: " + " ".join([str(i) for i in args])
        print(msg)

    @staticmethod
    def error(*args):
        """
        log any errors

        :param args: any error for logging
        """
        msg = f"{arrow.utcnow().isoformat()} -- ERROR -- : " + " ".join([str(i) for i in args])
        print(msg)


class Dict(dict):
    """
    dict class that allows dot notation
    """

    def __init__(self, *args, **kwargs):
        super(Dict, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    if isinstance(v, dict):
                        self[k] = Dict(v)
                    else:
                        self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                if isinstance(v, dict):
                    self[k] = Dict(v)
                else:
                    self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Dict, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Dict, self).__delitem__(key)
        del self.__dict__[key]


# TODO: work this out for detaching the procces from main loop
class Broadcaster:
    def __init__(self, socket):
        self.socket = socket

    def send(self, message, port=12345):
        guild = Dict({"id": None, "name": None}) if message.guild is None else message.guild
        channel = Dict({"id": message.channel.id, "name": "DM"}) \
            if isinstance(message.channel, discord.DMChannel) else message.channel
        package = {"sender":
                       {"id": message.author.id,
                        "name": message.author.name
                        },
                   "content": message.content,
                   "guild": {"name": guild.name,
                             "id": guild.id
                             },
                   "channel": {"name": channel.name,
                               "id": channel.id
                               }
                   }
        self.socket.sendto(json.dumps(package).encode(), ('255.255.255.255', port))

    def receive(self, bytes_to_receive=1024):
        rawMessage = self.socket.recvfrom(bytes_to_receive)[0]
        return json.loads(rawMessage.decode())


class DiscordInteractive:
    """
    run a command on the main async loop
    useful for discord interaction channel
    """
    loop: Optional[asyncio.AbstractEventLoop] = None

    def interact(self, command, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self.__executor(command, *args, **kwargs), self.loop)
        return future.result(600)

    async def __executor(self, command, *args, **kwargs):
        return await command(*args, **kwargs)


def sanitize(text: str) -> str:
    """
    remove all spacial characters from text

    :param text: input text
    :return: clean text
    """
    meta_characters = ["\\", "^", "$", "{", "}", "[",
                       "]", "(", ")", ".", "*", "+",
                       "?", "|", "<", ">", "-", "&",
                       "/", ",", "!"]
    output_string = text
    for i in meta_characters:
        if i in text:
            output_string = output_string.replace(i, "")  # "\\" + i)

    return output_string


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
                                      description=f"`{command_text}`", inline=False)

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


async def help_me(message_obj: discord.Message, command: str):
    """
    get help on command and post embed

    :param message_obj: a discord message object
    :param command: command to get help on
    """
    await getattr(commands, "help")().call({"message_obj": message_obj, "args": ["", command]})


def get_user(args: list, ign: Optional[str], platfrom: str) -> str:
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

    if name.startswith("<@") and name.endswith(">"):
        if name[2:-1] in Users.users.keys():
            try:
                return Users.users[name[2:-1]][platfrom + "_ign"]
            except IndexError:
                raise UserNonexistent

    return name


def fetch_emote(emote_name: str, guild: Union[None, discord.Guild], client: discord.Client) \
        -> Union[bool, discord.Emoji]:
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


def dict_string_to_nums(dictionary: dict) -> dict:
    """
    turns all strings that are numbers into numbers inside a dict

    :param dictionary: dict
    :return: dict
    """
    for i, j in dictionary.items():
        if isinstance(j, str) and j.replace(".", "", 1).isnumeric():
            num = float(j)
            if num.is_integer():
                num = int(num)

            dictionary[i] = num
    return dictionary


def format_nums(number: Union[float, int], decimals: int) -> Union[int, float]:
    """
    rounds to a number of decimals and if possible makes  a integer from float

    :param number: input number
    :param decimals: decimals to round to
    :return: integer or float
    """
    if round(float(number), decimals).is_integer():
        return int(f"{number:.0f}")

    return float(f"{number:.{decimals}f}")


SEPARATOR = "※"  # "✦"

DIGITS = regex.compile(r"^\D+(\d+)$")

DATE_FORM = "YYYY-MM-DD hh:mm:ss"
