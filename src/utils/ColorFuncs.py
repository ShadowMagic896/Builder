"""
Contains functions used in .Images and .Colors for manipulating array-like RBG color values
"""
# fmt: off
from typing import Set
import numpy as np
from src.utils.PythonUtil import concat


def merge(c1: np.ndarray, c2: np.ndarray, channel: str):
    result = tuple(map(lambda x: int(x), ((c1 + filter_channels(c2)) / 2).round()))
    return np.array(result)

def enforce_alpha(a1: np.ndarray, default_alpha: int = 255):
    """
    Ensures that the RBG array includes the Alpha component.
    """
    if a1.shape[1] == 4:
        return a1
    return np.array([concat(a1v, [default_alpha],) for a1v in a1.astype(int)])


def filter_channels(a1: np.ndarray, a2: np.ndarray, channels: Set[int]):
    """
    Copies values from `a2 to `a1` for each channel in `channels`
    """
    if a1.shape != a2.shape:
        raise ValueError("Arrays do not have same shape")
    return np.array([
        [(a2[val_co][chan_co] if chan_co in channels else a1[val_co][chan_co]) for chan_co in range(4)] 
        for val_co in range(len(a1))
    ]).reshape(*a1.shape)


def get_channels(channel: str, alpha: bool = True):
    """
    Gets a set of indicies from a channel string. Raises IndexError.
    Alpha: Whether to allow alpha values
    """
    channel = channel.upper()
    chandict = {"R": 0, "G": 1, "B": 2, "A": 3}
    try:
        return {chandict.pop(x) for x in (channel if alpha else channel.replace("A", ""))}
    except KeyError:
        raise ValueError("A channel name was repeated")


def toHex(rgb: np.ndarray) -> str:
    r, g, b = tuple(rgb)
    r = hex(r)[2:]
    g = hex(g)[2:]
    b = hex(b)[2:]

    r = (2 - len(r)) * "0" + r
    g = (2 - len(g)) * "0" + g
    b = (2 - len(b)) * "0" + b

    return f"#{r}{g}{b}"

# channels ="RBGA"
# chan_s = get_channels(channels)
# a1 = np.array([[0,0,0,0], [1,1,1,1]])
# a2 = np.array([[1,1,1,1], [0,0,0,0]])
# print(filter_channels(a1, a2, chan_s))
# a3 = np.array([[0,0,0], [1,2,3]])
# print(enforce_alpha(a3))
