import json


class Config:
    file = "config.json"

    prefix = ""
    debug = ""
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

    def load():
        with open(Config.file, "r") as configs:
            Config.close_dir(json.load(configs))

    def save():
        with open(Config.file, "w") as outfile:
            json.dump(Config.open_dir(), outfile)

    def open_dir():
        itms = dict()
        skip = ["file"]
        for i in dir(Config):
            if i in skip:
                pass
            elif not callable(getattr(Config, i)) and not i.startswith("__"):
                itms[i] = getattr(Config, i)
            elif isinstance(getattr(Config, i), type) and not i.startswith("__"):
                itms[i] = dict()
                for j in dir(getattr(Config, i)):
                    if not callable(getattr(getattr(Config, i), j)) and not j.startswith("__"):
                        itms[i][j] = getattr(getattr(Config, i), j)
        return itms

    def close_dir(info):
        for i, j in info.items():
            if not isinstance(getattr(Config, i), type):
                setattr(Config, i, j)
            else:
                for k, v in info[i].items():
                    setattr(getattr(Config, i), k, v)
