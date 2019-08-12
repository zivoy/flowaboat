import json
import os
from datetime import datetime
import commands
import discord


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
        with open(self.file, "r") as configs:
            self.close_dir(self.__class__, json.load(configs))

    def save(self):
        with open(self.file, "w") as outfile:
            json.dump(self.open_dir(self.__class__, ["file"]), outfile)


class Config(JasonFile):
    super(JasonFile)
    if not os.path.isfile("./config.json"):
        os.mknod("./config.json")
    file = "config.json"

    prefix = ""
    debug = ""
    administer = ""
    osu_cache_path = ""
    pp_path = ""
    beatmap_api = ""

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
    super(JasonFile)
    if not os.path.isfile("./users.list"):
        #os.mknod("./users.list")
        open("./users.list", 'w').close()
    file = "users.list"

    users = dict()

    def add_user(self, uuid, osu_ign="", steam_ign=""):
        if uuid not in self.users:
            self.users[uuid] = {"osu_ign": osu_ign, "steam_ign": steam_ign, "last_beatmap": None, "last_message": None}
            self.save()

    def set(self, uuid, item, value):
        self.users[uuid][item] = value
        self.save()


class Log:
    def log(*args):
        msg = f"{datetime.utcnow().isoformat()}: " + "".join([str(i) for i in args])
        print(msg)

    def error(*args):
        msg = f"{datetime.utcnow().isoformat()} -- ERROR -- : " + "".join([str(i) for i in args])
        print(msg)


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
    found = False
    for i, j in commands.List.items():
        if command == i or command in j:
            found = True
            command = getattr(commands, sanitize(i))()
            command_text = f"{Config.prefix}{i}"

            help_page = discord.Embed(title="Command", description=f"`{command_text}`", inline=False)

            if command.synonyms:
                help_page.add_field(name="Synonyms", value=", ".join([f"`{Config.prefix}{i}`" for i in command.synonyms]),
                                    inline=False)

            help_page.add_field(name="Description", value=command.description, inline=False)

            help_page.add_field(name="Usage", value=f"Required variables: {command.argsRequired}\n\
                                                      ```{command_text} {command.usage}```", inline=False)

            examples = command.examples
            emps = "s" if len(examples) > 1 else ""
            examps = "\n\n".join([f"```{Config.prefix}{i['run']}```{i['result']}" for i in examples])
            help_page.add_field(name="Example"+emps, value=examps, inline=False)

            return help_page

    if not found:
        return discord.Embed(title="ERROR", description="Command not found")
