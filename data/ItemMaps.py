from pprint import pprint
from typing import Mapping
from chempy.util import periodic

class Chemistry():
    def __init__(self):
        self.symbols = periodic.symbols
        self.names = periodic.names
        self.sym_to_name: Mapping[str, (str, int)] = {
            tup[0].lower(): (tup[1].lower(), c) 
            for c, tup in 
            enumerate([
                (periodic.symbols[a], periodic.names[a]) 
                for a in range(len(periodic.symbols))
            ])
        }
        self.name_to_sym: Mapping[str, (str, int)] = {
            tup[1][0].lower(): (tup[0].lower(), tup[1][1])
            for tup in list(self.sym_to_name.items())
        }
    

Chemistry()