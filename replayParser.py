import pandas as pd
import lzma
from io import StringIO
from base64 import b64decode


def lzma_to_pd(lzma_byte_string):
    stream = lzma.decompress(lzma_byte_string)
    dataframe = pd.read_csv(StringIO(str(stream)[2:-1]), sep="|", lineterminator=',', header=None)
    dataframe.columns = ["ms since last", "x pos", "y pos", "clicks"]
    return dataframe


def replay_string_to_pd(replay):
    byte_string = b64decode(replay)
    dataframe = lzma_to_pd(byte_string)
    return dataframe
