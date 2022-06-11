from os import PathLike
from typing import Any, Callable, List, Set

from src.utils.Checks import interactionChoke

# Directories to look for cogs in
COG_DIRECTORIES: List[PathLike] = [
    "./src/cogs/development",
    "./src/cogs/economy",
    "./src/cogs/main",
    "./src/cogs/api",
]

# Cogs to not load on startup
NOLOAD_COGS: List[str] = []

# ALl cogs to load on startup
SOURCE_CODE_PATHS: List[PathLike] = ["./data", "./src"]

# All command prefixes that the bot should respond to
PREFIXES: Set[str] = {">>"}

# Whether to execute load_extensions on startup
LOAD_COGS_ON_STARTUP: bool = True

# Cogs that do not show up on help command
INVISIBLE_COGS: List[str] = ["ErrorHandling", "Help", "Dev", "GitHub"]

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
CATCH_ERRORS: bool = False

# Whether to catch  errors in text commands / hybrid commands
CATCH_COMMAND_ERRORS: bool = True and CATCH_ERRORS

# Whether to catch errors in app commands
CATCH_COMMAND_TREE_ERRORS: bool = True and CATCH_ERRORS


# Errors on events / event listeners
PRINT_EVENT_ERROR_TRACEACK: bool = False and CATCH_ERRORS

# Errors in text commands / hybrid commands
PRINT_COMMAND_ERROR_TRACKEBACK: bool = False and CATCH_ERRORS

# Errors in app commands
PRINT_COMMAND_TREE_ERROR_TRACKEBACK: bool = False and CATCH_ERRORS


# Checks that are applied on every command
GLOBAL_CHECKS: List[Callable[[Any], bool]] = [
    interactionChoke,
]

# Commands that are exempt from global checks, in string form. The string should be the fully qualified name of the command
IGNORED_GLOBALLY_CHECKED_COMMANDS: List[str] = []

# Whether to force all commands of a group to inherit all checks of the group
INHERIT_GROUP_CHECKS: bool = True

# A list of checks to NOT inherit, if `INHERIT_GROUP_CHECKS` is true.
IGNORED_INHERITED_GROUP_CHECKS: List[Callable[[Any], bool]] = []

EVALUATION_FILE_THRESHOLD = 4000
EVALUATION_TRUNCATION_THRESHOLD = 20000
