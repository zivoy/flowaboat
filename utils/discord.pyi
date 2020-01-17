import asyncio
import socket
from typing import Optional, Union, NoReturn, TypedDict, List, Tuple

import arrow
import discord


class _Property(TypedDict):
    id: int
    name: str


class _Message(TypedDict):
    sender: _Property
    content: str
    message_id: int
    guild: _Property
    channel: _Property


class Broadcaster:
    def __init__(self, connection_socket: socket.socket): ...

    socket: socket.socket

    def send(self, message: discord.Message = ..., port: int = ...) -> NoReturn: ...

    def receive(self, bytes_to_receive: int = ...) -> _Message: ...

    @staticmethod
    def is_by_author(original: Union[discord.Message, _Message], new: _Message) -> bool: ...


class DiscordInteractive:
    loop: Optional[asyncio.AbstractEventLoop]
    client: Optional[discord.Client]

    @classmethod
    def interact(cls, command, *args, **kwargs): ...

    @staticmethod
    def __executor(command, *args, **kwargs): ...

class Question:
    def __init__(self, listener: Broadcaster, original_message: discord.Message, sender: discord.Message): ...
    original: discord.Message
    listener: Broadcaster
    sender: discord.Message
    def multiple_choice(self, question: str, option_list: List[str]) -> Union[bool, int]: ...
    def get_real_number(self, question: str = ..., is_integer: bool = ..., is_positive: bool = ...,
                        minimum: Optional[Union[int,float]] = ..., maximum: Optional[Union[int,float]] = ...)\
            -> Union[bool, float, int]: ...
    @staticmethod
    def stop_check(user_input: _Message) -> bool: ...
    def get_string(self, question: str, confirm: bool = ...) -> Union[bool, str]: ...

    async def _delete_messages(self, messages: List[int]) -> NoReturn: ...
    def delete_messages(self, messages: List[int]) -> NoReturn: ...
    def get_date(self, question: str, required: bool = ..., tzinfo: Optional[int] = ...) \
            -> Tuple[arrow.Arrow, Optional[int]] : ...






def command_help(command: str) -> discord.Embed: ...
async def help_me(message_obj: discord.Message, command: str): ...
def fetch_emote(emote_name: str, guild: Optional[discord.Guild], client: discord.Client) \
        -> Union[bool, discord.Emoji]: ...
def get_user(args: list, ign: Optional[str], platfrom: str) -> str: ...
