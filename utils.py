import json
import os
import commands
import discord
import requests
import regex
import arrow
import math


class Api:
    def __init__(self, base_url, params=dict()):
        self.url = base_url
        self.params = params

    def get(self, url, params=None, **kwargs):
        url = self.url + url
        if params is not None:
            for k, j in self.params.items():
                params[k] = j
        elif self.params != {}:
            params = self.params

        return requests.get(url, params, **kwargs)


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
    debug = ""
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
                                "last_beatmap": {"map": (None, None), "mods": [], "completion": 0, "acc": 0},
                                "last_message": None}
            self.save()

    def set(self, uuid, item, value):
        self.users[str(uuid)][item] = value
        self.save()


#


Config().load()
Users().load()

#


class Loging:
    def log(self, *args):
        msg = f"{arrow.utcnow().isoformat()}: " + " ".join([str(i) for i in args])
        print(msg)

    def error(self, *args):
        msg = f"{arrow.utcnow().isoformat()} -- ERROR -- : " + " ".join([str(i) for i in args])
        print(msg)


Log = Loging()


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

            help_page = discord.Embed(title="Command", description=f"`{command_text}`", inline=False)

            if command.synonyms:
                help_page.add_field(name="Synonyms",
                                    value=", ".join([f"`{Config.prefix}{i}`" for i in command.synonyms]), inline=False)

            help_page.add_field(name="Description", value=command.description, inline=False)

            help_page.add_field(name="Usage", value=f"**Required variables**: `{command.argsRequired}`\n"
                                                    f"```{command_text} {command.usage}```", inline=False)

            examples = command.examples
            emps = "s" if len(examples) > 1 else ""
            examps = "\n\n".join([f"```{Config.prefix}{i['run']}```{i['result']}" for i in examples])
            help_page.add_field(name="Example"+emps, value=examps, inline=False)

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
            return Users.users[name[2:-1]][platfrom+"_ign"]

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


separator = "✦"

digits = regex.compile(r"^\D+(\d+)$")

date_form = "YYYY-MM-DD hh:mm:ss"
