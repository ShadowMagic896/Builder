from typing import Iterable

import numpy as np


def concat(a1: Iterable, a2: Iterable):
    a1 = list(a1)
    a1.extend(list(a2))
    return np.array(a1)
