from typing import Union, Optional, NoReturn, List

import arrow
import requests


class Api:
    def __init__(self, base_url: str = ..., max_requests_per_minute: int = ..., params: Optional[dict] = ...): ...
    url: str
    params: dict
    max_requests: int
    actions: List[arrow.Arrow]

    def get(self, url: str, params: Optional[dict] = ..., **kwargs) -> requests.Response: ...

    def clear_queue(self):...


class Log:
    @staticmethod
    def log(*args) -> NoReturn: ...

    @staticmethod
    def error(*args) -> NoReturn: ...


class PickeledServerDict:
    def __init__(self, file: str, dictionary: Optional[dict] = ...): ...
    dictionary: Dict[dict]
    file: str
    def load(self): ...
    def save(self): ...


class Dict(dict): ...


def sanitize(text: str) -> str: ...


def dict_string_to_nums(dictionary: dict) -> dict: ...


def format_nums(number: Union[float, int], decimals: int) -> Union[int, float]: ...

def validate_date(date_text: str, date_format: str, **kwargs) -> Union[bool,arrow.Arrow]: ...
