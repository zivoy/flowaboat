import pandas as pd
import lzma
from io import StringIO
from base64 import b64decode
from urllib.request import urlopen, Request


def lzma_replay_to_df(lzma_byte_string):
    stream = lzma.decompress(lzma_byte_string)
    dataframe = info_string_to_df(stream)
    dataframe.columns = ["ms since last", "x pos", "y pos", "clicks"]
    dataframe['offset'] = dataframe["ms since last"].cumsum()
    return dataframe


def info_string_to_df(info):
    dataframe = pd.read_csv(StringIO(str(info)[2:-1]), sep="|", lineterminator=',', header=None)
    return dataframe


def replay_string_to_df(replay):
    byte_string = b64decode(replay)
    dataframe = lzma_replay_to_df(byte_string)
    return dataframe


def open_file(file_name):
    with open(file_name, "rb") as replay:
        return ParseReplayByteSting(replay.read())


def open_link(link):
    with urlopen(Request(link,
                         headers={'User-Agent': 'Mozilla/5.0'})) as replay:
        return ParseReplayByteSting(replay.read())


class ParseReplayByteSting:
    def __init__(self, byte_string):
        byte_string, self.gamemode = get_byte(byte_string)
        byte_string, self.game_version = get_integer(byte_string)
        byte_string, self.map_md5_hash = get_string(byte_string)
        byte_string, self.player_name = get_string(byte_string)
        byte_string, self.replay_md5_hash = get_string(byte_string)

        byte_string, self.count300 = get_short(byte_string)
        byte_string, self.count100 = get_short(byte_string)
        byte_string, self.count50 = get_short(byte_string)
        byte_string, self.countgekis = get_short(byte_string)
        byte_string, self.countkatus = get_short(byte_string)
        byte_string, self.countmisses = get_short(byte_string)

        byte_string, self.final_score = get_integer(byte_string)
        byte_string, self.max_combo = get_short(byte_string)
        byte_string, self.perfect = get_byte(byte_string)
        byte_string, self.mods = get_integer(byte_string)

        byte_string, life_graph = get_string(byte_string)
        self.life_graph = info_string_to_df(life_graph)
        self.life_graph.columns = ["offset", "health"]

        byte_string, self.time_stamp = get_long(byte_string)

        byte_string, replay_length = get_integer(byte_string)
        self.replay = lzma_replay_to_df(byte_string[:replay_length])
        byte_string = byte_string[replay_length:]
        self.seed = 0
        if self.replay["ms since last"].iloc[-1] == -12345:
            self.seed = int(self.replay["clicks"].iloc[-1])
            self.replay.drop(self.replay.tail(1).index, inplace=True)

        _, self.score_id = get_integer(byte_string)


def get_byte(byte_str):
    byte = byte_str[0]
    byte_str = byte_str[1:]
    return byte_str, byte


def get_short(byte_str):
    short = int.from_bytes(byte_str[:2], byteorder="little")
    byte_str = byte_str[2:]
    return byte_str, short


def get_integer(byte_str):
    integer = int.from_bytes(byte_str[:4], byteorder="little")
    byte_str = byte_str[4:]
    return byte_str, integer


def get_long(byte_str):
    long = int.from_bytes(byte_str[:8], byteorder="little")
    byte_str = byte_str[8:]
    return byte_str, long


def get_uleb126(byte_str):
    uleb_parts = []
    while byte_str[0] >= 0x80:
        uleb_parts.append(byte_str[0] - 0x80)
        byte_str = byte_str[1:]
    uleb_parts.append(byte_str[0])
    byte_str = byte_str[1:]
    uleb_parts = uleb_parts[::-1]
    integer = 0
    for i in range(len(uleb_parts) - 1):
        integer = (integer + uleb_parts[i]) << 7
    integer += uleb_parts[-1]
    return byte_str, integer


def get_string(byte_str):
    fb, byte_str = byte_str[0], byte_str[1:]
    if fb == 0:
        return byte_str, ""

    byte_str, length = get_uleb126(byte_str)
    string = str(byte_str[:length])[2:-1]
    byte_str = byte_str[length:]
    return byte_str, string


def test_get_string():
    c = bytes([0, 65])
    a, b = get_string(c)
    print(a, b)

    c = bytes([11, 5, 65, 65, 64, 65, 65, 65, 67])
    a, b = get_string(c)
    print(a, b)


test_get_string()


def calculate_unstable_rate(replay_dataframe, beatmap_obj, speed=1):
    pass
    # TODO
