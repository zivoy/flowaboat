import json
import os
from time import sleep

import arrow
import discord
import regex
import requests
import socket

import commands


class UserError(Exception):
    pass


class UserNonexistent(UserError):
    pass


class Api:
    def __init__(self, base_url, max_requests_per_minute, params=dict()):
        self.url = base_url
        self.params = params
        self.max_requests = max_requests_per_minute
        self.actions = list()

    def clear_queue(self):
        for i in self.actions.copy():
            if (arrow.utcnow() - i).seconds >= 60:
                self.actions.pop(0)
            else:
                break

    def get(self, url, params=None, **kwargs):
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
        else:
            sleep(max(60.1 - (arrow.utcnow() - self.actions[0]).seconds, 0))
            return self.get(url, params, **kwargs)


class JasonFile:
    file = ""

    def open_dir(self, obj, skip=list(), itms=dict()):
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
        for i, j in info.items():
            if not isinstance(getattr(obj, i), type):
                setattr(obj, i, j)
            else:
                self.close_dir(getattr(obj, i), info[i])

    def load(self):
        if not os.path.isfile(self.file):
            # os.mknod(self.file)
            open(self.file, "w").close()
            self.save()
        with open(self.file, "r") as configs:
            self.close_dir(self.__class__, json.load(configs))

    def save(self):
        with open(self.file, "w") as outfile:
            json.dump(self.open_dir(self.__class__, ["file"]), outfile, indent="  ", sort_keys=True)


class Config(JasonFile):
    file = "config.json"

    prefix = ""
    debug = False
    administer = ""
    osu_cache_path = ""
    pp_path = ""

    class credentials:
        bot_token = ""
        discord_client_id = ""
        osu_api_key = ""
        twitch_client_id = ""
        pexels_key = ""
        last_fm_key = ""

    class logsCredentials:
        rawPassword = ""
        encPassword = ""


class Users(JasonFile):
    file = "users.list"

    users = dict()

    def add_user(self, uuid, osu_ign="", steam_ign=""):
        uuid = str(uuid)
        if uuid not in self.users:
            self.users[uuid] = {"osu_ign": osu_ign, "steam_ign": steam_ign,
                                "last_beatmap": {"map": (None, ""), "mods": [],
                                                 "completion": 0, "accuracy": 0,
                                                 "user": osu_ign, "replay": None},
                                "last_message": None}
            self.save()

    def set(self, uuid, item, value):
        self.users[str(uuid)][item] = value
        self.save()

    def update_last_message(self, user, map_link, map_type, mods,
                            completion, accuracy, user_ign, replay):
        self.set(user, "last_beatmap",
                 {"map": (map_link, map_type), "mods": mods,
                  "completion": completion, "accuracy": accuracy,
                  "user": user_ign, "replay": replay})


#


Config().load()
Users().load()


#


class Log:
    @staticmethod
    def log(*args):
        msg = f"{arrow.utcnow().isoformat()}: " + " ".join([str(i) for i in args])
        print(msg)

    @staticmethod
    def error(*args):
        msg = f"{arrow.utcnow().isoformat()} -- ERROR -- : " + " ".join([str(i) for i in args])
        print(msg)


class Dict(dict):
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


class Broadcaster:
    def __init__(self, socket):
        self.socket = socket

    def send(self, message, port=12345):
        guild = Dict({"id": None, "name": None}) if message.guild is None else message.guild
        channel = Dict({"id": message.channel.id, "name": "DM"}) if isinstance(message.channel, discord.DMChannel) \
            else message.channel
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


def sanitize(text):
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


async def help_me(message_obj, command):
    await getattr(commands, "help")().call({"message_obj": message_obj, "args": ["", command]})


def get_user(args, ign, platfrom):
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


def fetch_emote(emote_name, guild, client):
    e_lists = []
    if guild:
        e_lists.extend(guild.emojis)
    e_lists.extend(client.emojis)
    valid = [x for x in e_lists if x.name.lower() == emote_name.lower()]
    if not valid:
        Log.error("Not valid emote")
        return False
    return valid[0]


def dict_string_to_nums(dictionary):
    for i, j in dictionary.items():
        if type(j) == str and j.replace(".", "", 1).isnumeric():
            num = float(j)
            if num.is_integer():
                num = int(num)

            dictionary[i] = num
    return dictionary


def format_nums(number, decimals):
    if round(float(number), decimals).is_integer():
        return int(f"{number:.0f}")
    else:
        return float(f"{number:.{decimals}f}")


separator = "✦"

digits = regex.compile(r"^\D+(\d+)$")

date_form = "YYYY-MM-DD hh:mm:ss"
