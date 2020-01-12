import json
import os


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
    file = "./config/config.json"

    prefix = ""
    debug = False
    administer = False
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


# todo: have each user be its separate file // maybe also pickling
class Users(JasonFile):
    """
    stores some information on users
    """
    file = "./config/users.list"

    users = dict()

    def add_user(self, uuid, osu_ign="", steam_ign=""):
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

    def set(self, uuid, item, value):
        """
        updates user data
        :param uuid: discord id
        :param item: item to change
        :param value: value to be set to
        """
        self.users[str(uuid)][item] = value
        self.save()

    def update_last_message(self, user, map_link, map_type, mods, completion, accuracy, user_ign, replay):
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


Config().load()
Users().load()
