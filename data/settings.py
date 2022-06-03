from os import PathLike
from typing import List, Set, Tuple

# Directories of cogs to load
COG_DIRECTORIES: List[PathLike] = [
    "./src/cogs/development",
    "./src/cogs/economy",
    "./src/cogs/main",
]

NOLOAD_COGS: List[PathLike] = []

SOURCE_CODE_PATHS: List[PathLike] = ["./data", "./src"]

PREFIXES: Set[str] = {">>"}

LOAD_COGS_ON_STARTUP: bool = True
SHOW_SOURCE_LINES: bool = True

LOAD_JISHAKU: bool = False
MODERATE_JISHAKU_COMMANDS: bool = False

STARTUP_ENSURE_DEFAULT_ATOMS: bool = True

STARTUP_UPDATE_COMMANDS: bool = True
STARTUP_ADD_HIDDEN_COMMANDS: bool = True

CATCH_ERRORS: bool = True
PRINT_EVENT_ERROR_TRACEACK: bool = True
PRINT_COMMAND_ERROR_TRACKEBACK: bool = True
