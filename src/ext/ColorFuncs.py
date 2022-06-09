import numpy as np


def merge(c1: np.ndarray, c2: np.ndarray, channel: str):
    result = tuple(map(lambda x: int(x), ((c1 + filterChannels(c2)) / 2).round()))
    return np.array(result)


def filterChannels(c1: np.ndarray, c2: np.ndarray, channel: str, alpha: bool = False):
    """
    Copies values from C2 to C1 for each channel
    """
    return np.array(
        [(x if c in getChannels(channel, alpha) else c1[c]) for c, x in enumerate(c2)]
    )


def getChannels(channel: str, alpha: bool):
    chandict = {"R": 0, "G": 1, "B": 2, "A": 3 if alpha else -1}
    channels = {chandict.pop(x) for x in channel}
    return channels


def toHex(rgb: np.ndarray) -> str:
    r, g, b = tuple(rgb)
    r = hex(r)[2:]
    g = hex(g)[2:]
    b = hex(b)[2:]

    r = (2 - len(r)) * "0" + r
    g = (2 - len(g)) * "0" + g
    b = (2 - len(b)) * "0" + b

    return f"#{r}{g}{b}"
