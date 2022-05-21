from pprint import pprint
from typing import Mapping
from chempy.util import periodic


class Chemistry:
    def __init__(self):
        self.symbols = periodic.symbols
        self.names = periodic.names
        self.sym_to_name: Mapping[str, (str, int)] = {
            tup[0].capitalize(): (tup[1].capitalize(), c)
            for c, tup in enumerate(
                [
                    (periodic.symbols[a], periodic.names[a])
                    for a in range(len(periodic.symbols))
                ]
            )
        }
        self.name_to_sym: Mapping[str, (str, int)] = {
            tup[1][0].capitalize(): (tup[0].capitalize(), tup[1][1])
            for tup in list(self.sym_to_name.items())
        }


def getAtomicName(item: str):
    """
    Finds the name of an atom from either its name, symbol, or atomic number.
    """
    chem = Chemistry()
    item: str = str(item).capitalize()
    if (_item := chem.sym_to_name.get(item, None)) is None:  # Check if not full name
        if (_item := chem.name_to_sym.get(item, None)) is None:  # Check if not symbol
            if not (_item := item.isdigit()):
                raise ValueError("Invalid element: Not name, symbol, or atomic number.")
            else:
                item = int(item)
                if item < 1 or item > len(periodic.names):
                    raise ValueError("Invalid element: Invalid atomic number")
                else:
                    item = periodic.names[item - 1]
        else:
            item = chem.sym_to_name.get(_item[0])[0]
    else:
        item = _item[0]
    return item
