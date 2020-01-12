from io import BytesIO
from typing import Union

import numpy as np

from .stating import MapStats, get_strains


def graph_bpm(map_obj: MapStats = ...) -> BytesIO: ...


def map_strain_graph(map_strains: get_strains, progress: float = ..., width: float = ..., height: float = ...,
                     max_chunks: Union[int, float] = ..., low_cut: float = ...) -> BytesIO: ...


def avgpt(points: Union[list, np.array], index: int) -> float:
