import asyncio
import socket
from typing import Optional, Union, NoReturn, TypedDict

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
    def is_by_author(original: discord.Message, new: _Message) -> bool: ...


class DiscordInteractive:
    loop: Optional[asyncio.AbstractEventLoop]

    @classmethod
    def interact(cls, command, *args, **kwargs): ...

    @staticmethod
    def __executor(command, *args, **kwargs): ...


def command_help(command: str) -> discord.Embed: ...


def help_me(message_obj: discord.Message, command: str): ...


def fetch_emote(emote_name: str, guild: Optional[discord.Guild], client: discord.Client) \
        -> Union[bool, discord.Emoji]: ...


def get_user(args: list, ign: Optional[str], platfrom: str) -> str: ...
