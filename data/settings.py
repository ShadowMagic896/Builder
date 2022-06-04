from os import PathLike
from typing import List, Set

COG_DIRECTORIES: List[PathLike] = [
    "./src/cogs/development",
    "./src/cogs/economy",
    "./src/cogs/main",
]  # Directories to look for cogs in

NOLOAD_COGS: List[PathLike] = []  # Cogs to not load on startup

SOURCE_CODE_PATHS: List[PathLike] = ["./data", "./src"]  # Whether

PREFIXES: Set[str] = {">>"}  # All command prefixes that the bot should respond to

LOAD_COGS_ON_STARTUP: bool = True  # Whether to execute load_extensions on startup
SHOW_SOURCE_LINES: bool = (
    True  # Whether to set the bot's status to the amount of source lines
)

LOAD_JISHAKU: bool = False  # Whether to load the Jishaku Cog
MODERATE_JISHAKU_COMMANDS: bool = (
    False  # Whether to moderate commands from the Jishaku Cog
)

STARTUP_ENSURE_DEFAULT_ATOMS: bool = (
    False  # Whether to recreate the atoms database on startup
)

STARTUP_UPDATE_COMMANDS: bool = True  # Whether to update command database on startup

CATCH_ERRORS: bool = True  # Whether to apply all error-catching functions to the bot
PRINT_EVENT_ERROR_TRACEACK: bool = (
    True and CATCH_ERRORS
)  # Errors on events / event listeners
PRINT_COMMAND_ERROR_TRACKEBACK: bool = (
    True and CATCH_ERRORS
)  # Errors in text commands / hybrid commands
PRINT_COMMAND_TREE_ERROR_TRACKEBACK: bool = (
    True and CATCH_ERRORS
)  # Errors in app commands
