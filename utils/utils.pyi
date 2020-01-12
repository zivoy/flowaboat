from typing import Union, Optional, NoReturn

import requests


class Api:
    def __init__(self, base_url: str = ..., max_requests_per_minute: int = ..., params: Optional[dict] = ...): ...

    def get(self, url: str, params: Optional[dict] = ..., **kwargs) -> requests.Response: ...


class Log:
    @staticmethod
    def log(*args) -> NoReturn: ...

    @staticmethod
    def error(*args) -> NoReturn:


def sanitize(text: str) -> str: ...


def dict_string_to_nums(dictionary: dict) -> dict: ...


def format_nums(number: Union[float, int], decimals: int) -> Union[int, float]: ...
