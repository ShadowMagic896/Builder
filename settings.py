import logging
from os import PathLike
from typing import Any, Callable, List, Set

from discord.ext import commands

from src.utils.checks import inter_choke

# Directories to look for cogs in
EXT_DIRECTORIES: List[PathLike] = ["./src/cogs"]

# Cogs to not load on startup
NOLOAD_EXTS: List[str] = []

# ALl cogs to load on startup
SOURCE_CODE_PATHS: List[PathLike] = ["."]

# All command prefixes that the bot should respond to
PREFIXES: Set[str] = {">>"}

# Whether to execute load_extensions on startup
LOAD_COGS_ON_STARTUP: bool = True

# Whether to start docker on startup
START_DOCKER_ON_STARTUP: bool = False

# Location of docker desktop to run
DOCKER_DESKTOP_LOCATION: str = "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"

# Cogs that do not show up on help command
INVISIBLE_COGS: List[str] = ["ErrorHandling", "Help", "Dev"]

# Whether to set the bot's status to the amount of source lines
SHOW_SOURCE_LINES: bool = True

# Whether to load the Jishaku Cog
LOAD_JISHAKU: bool = False

# Whether to moderate commands from the Jishaku Cog
MODERATE_JISHAKU_COMMANDS: bool = False

# Whether to recreate the atoms database on startup
STARTUP_ENSURE_DEFAULT_ATOMS: bool = False

# Whether to update command database on startup
STARTUP_UPDATE_COMMANDS: bool = True

# Whether to apply all error-catching functions to the bot
CATCH_ERRORS: bool = True

# Errors on events / event listeners
PRINT_EVENT_ERROR_TRACEACK: bool = False and CATCH_ERRORS

# Errors in text commands / hybrid commands
PRINT_COMMAND_ERROR_TRACKEBACK: bool = False and CATCH_ERRORS

# Errors in app commands
PRINT_COMMAND_TREE_ERROR_TRACKEBACK: bool = False and CATCH_ERRORS


# Checks that are applied on every command
GLOBAL_CHECKS: List[Callable[[commands.Context], bool]] = [
    inter_choke,
]

# Commands that are exempt from global checks, in string form. The string
# should be the fully qualified name of the command
IGNORED_GLOBALLY_CHECKED_COMMANDS: List[str] = []

# Whether to force all commands of a group to inherit all checks of the group
INHERIT_GROUP_CHECKS: bool = True

# A list of checks to NOT inherit, if `INHERIT_GROUP_CHECKS` is true.
IGNORED_INHERITED_GROUP_CHECKS: List[Callable[[Any], bool]] = []

# When to truncate /eval files (characters)
EVALUATION_TRUNCATION_THRESHOLD = 20000

# Guils to enable dev commands in
DEVELOPMENT_GUILD_IDS: List[int] = [871913539936329768]  # Bot Testing Server

BLACKLIST_USERS: List[int] = []

LOGGING_LEVEL: int = logging.DEBUG

# 1 use per 5 seconds
GLOBAL_COOLDOWN = (1, 5)
