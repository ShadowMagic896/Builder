"""
Contains functions used in .Images and .Colors for manipulating array-like RBG color values
"""
# fmt: off
import numpy as np
from typing import Set

from .python_util import concat


def merge(c1: np.ndarray, c2: np.ndarray, channels: Set[int]) -> np.ndarray:
    return np.array([round((c1[bchan] + c2[bchan]) / 2) if bchan in channels else c1[bchan] for bchan in range(4)])

def enforce_alpha(a1: np.ndarray, default_alpha: int = 255):
    """
    Ensures that the RBG array includes the Alpha component.
    """
    if a1.shape[1] == 4:
        return a1
    return np.array([concat(a1v, [default_alpha],) for a1v in a1.astype(int)])


def to_hex(rgb: np.ndarray) -> str:
    r, g, b = tuple(rgb)
    r = hex(r)[2:]
    g = hex(g)[2:]
    b = hex(b)[2:]

    r = (2 - len(r)) * "0" + r
    g = (2 - len(g)) * "0" + g
    b = (2 - len(b)) * "0" + b

    return f"#{r}{g}{b}"


def channels_to_names(indicies: Set[int]):
    return ", ".join(
            {{0: "Red", 1: "Green", 2: "Blue", 3: "Alpha"}.get(c, "Unknown... lol") for c in indicies}
        )

def names_to_channels(name: str):
    value = name.strip(" ,.").replace(" ", "")
    values = value.split(",")
    values = np.array(values, dtype=int)
    if len(values) == 3:
        av = list(values)
        av.append(255)
        values = np.array(av)
    elif len(values) != 4:
        raise ValueError(
            f"Invalid amount of colors given, expected 3 or 4. Got: {len(values)}"
        )
    return values
