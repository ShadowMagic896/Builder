from os import PathLike
from typing import List, Tuple


COG_DIRECTORIES: List[PathLike] = [
    "./src/cogs/development",
    "./src/cogs/economy",
    "./src/cogs/main",
]

NOLOAD_COGS: List[PathLike] = []

SOURCE_CODE_PATHS: List[PathLike] = ["./data", "./src"]

PREFIXES: Tuple[str] = ">>"

LOAD_COGS_ON_STARTUP: bool = True
SHOW_SOURCE_LINES: bool = True
LOAD_JISHAKU: bool = False

MODERATE_JISHAKU_COMMANDS: bool = False
CATCH_ERRORS: bool = True
