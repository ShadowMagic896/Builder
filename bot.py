from multiprocessing import freeze_support
import time
from typing import Iterable, Union, List, Any, Optional, Dict
import aiohttp
import discord
from discord import Interaction
from discord.ext import commands
from discord.ext.commands import Command, Parameter
from discord.ext.commands.view import StringView
import asyncio
import logging

import openai

from src.utils.Extensions import load_extensions
from src.utils.Functions import (
    apply_global_checks,
    aquire_connection,
    format_code,
    startupPrint,
)
from src.utils.Database import ensure_database
from src.utils.Stats import Stats
from data.Environ import BOT_KEY, OPENAI_KEY
from data.Settings import (
    COG_DIRECTORIES,
    LOAD_COGS_ON_STARTUP,
    LOAD_JISHAKU,
    PREFIXES,
    SHOW_SOURCE_LINES,
    SOURCE_CODE_PATHS,
    START_DOCKER_ON_STARTUP,
)
from src.utils.External import snekbox_exec

# Logging ---------------------------------------------------
logger = logging.getLogger("discord")
logger.setLevel(logging.ERROR)

filename = "data\\logs\\_discord.log"
encoding = "UTF-8"
mode = "w"

handler = logging.FileHandler(filename=filename, encoding=encoding, mode=mode)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
# -----------------------------------------------------------


class Builder(commands.Bot):
    def __init__(self):
        command_prefix: Iterable[str] = PREFIXES
        help_command: Union[commands.HelpCommand, None] = None
        tree_cls: type = discord.app_commands.CommandTree
        intents: discord.Intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        if SHOW_SOURCE_LINES:
            activity: discord.Activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{Stats.lineCount(SOURCE_CODE_PATHS)} LINES",
            )
        else:
            activity: discord.Activity = None
        application_id: str = "963411905018466314"
        case_insensitive: bool = True

        super().__init__(
            command_prefix=command_prefix,
            help_command=help_command,
            tree_cls=tree_cls,
            intents=intents,
            activity=activity,
            application_id=application_id,
            case_insensitive=case_insensitive,
        )
        status: str = "idle"
        self.status = discord.Status(status)
        self.tree.fallback_to_global = False
        self.openai = openai
        self.openai.api_key = OPENAI_KEY

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.start_unix = time.time()

    async def setup_hook(self) -> None:
        await startupPrint(self)


class BuilderContext(commands.Context):
    def __init__(
        self,
        *,
        message: discord.Message,
        bot: Builder,
        view: StringView,
        args: List[Any] = ...,
        kwargs: Dict[str, Any] = ...,
        prefix: Optional[str] = None,
        command: Optional[Command[Any, ..., Any]] = None,
        invoked_with: Optional[str] = None,
        invoked_parents: List[str] = ...,
        invoked_subcommand: Optional[Command[Any, ..., Any]] = None,
        subcommand_passed: Optional[str] = None,
        command_failed: bool = False,
        current_parameter: Optional[Parameter] = None,
        current_argument: Optional[str] = None,
        interaction: Optional[Interaction] = None,
    ):
        self.bot = bot
        super().__init__(
            message=message,
            bot=bot,
            view=view,
            args=args,
            kwargs=kwargs,
            prefix=prefix,
            command=command,
            invoked_with=invoked_with,
            invoked_parents=invoked_parents,
            invoked_subcommand=invoked_subcommand,
            subcommand_passed=subcommand_passed,
            command_failed=command_failed,
            current_parameter=current_parameter,
            current_argument=current_argument,
            interaction=interaction,
        )


async def main():
    bot: commands.Bot = Builder()
    if LOAD_JISHAKU:
        await bot.load_extension("jishaku")

    if LOAD_COGS_ON_STARTUP:
        await load_extensions(
            bot, COG_DIRECTORIES, spaces=20, ignore_errors=False, print_log=False
        )

    bot.apg = await aquire_connection()

    await ensure_database(bot)
    await format_code()
    if START_DOCKER_ON_STARTUP:
        await snekbox_exec()
    await apply_global_checks(bot)

    await bot.start(BOT_KEY)


if __name__ == "__main__":
    freeze_support()
    asyncio.run(main())
