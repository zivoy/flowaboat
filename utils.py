import json, os


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
        print(*args)

    def error(*args):
        print(*args)
