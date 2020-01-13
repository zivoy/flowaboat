from typing import Optional, List, NoReturn, Union


class JasonFile:
    file: str

    def open_dir(self, obj: JasonFile, skip: Optional[List[str]] = ..., itms: Optional[dict] = ...) -> dict: ...

    def close_dir(self, obj: JasonFile = ..., info: dict = ...) -> NoReturn: ...

    def load(self): ...

    def save(self): ...

class Config(JasonFile):
    prefix: str
    debug: bool
    administer: bool
    osu_cache_path: str
    pp_path: str

    class credentials:
        bot_token: str
        discord_client_id: str
        osu_api_key: str
        twitch_client_id: str
        pexels_key: str
        last_fm_key: str

    class logsCredentials:
        rawPassword: str
        encPassword: str


class Users():
    users: dict

    def add_user(self, uuid: str = ..., osu_ign: str = ..., steam_ign: str = ...) -> NoReturn: ...

    def set(self, uuid: str = ..., item=..., value=...) -> NoReturn: ...

    def update_last_message(self, user: Union[str, int], map_link: Union[int, str], map_type: str,
                            mods: List[str], completion: float, accuracy: float, user_ign: str, replay) \
            -> NoReturn: ...
