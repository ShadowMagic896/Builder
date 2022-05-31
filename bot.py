from asyncio.subprocess import PIPE, Process
from multiprocessing import freeze_support
from os import PathLike
from typing import Callable, List, Literal, Optional, Union
from urllib.parse import quote_plus
import aiohttp
import asyncpg
import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

import asyncio
import logging

from src.auxiliary.bot.Extensions import load_extensions
from src.auxiliary.bot.Functions import ensureDB, formatCode, startupPrint
from src.auxiliary.bot.Stats import Stats
from data.config import BOT_KEY, DB_PASSWORD, DB_USERNAME
from data.settings import (
    COG_DIRECTORIES,
    LOAD_COGS_ON_STARTUP,
    LOAD_JISHAKU,
    PREFIXES,
    SHOW_SOURCE_LINES,
    SOURCE_CODE_PATHS,
)

# Logging ---------------------------------------------------
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

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
        command_prefix: List[str] = when_mentioned_or(*PREFIXES)
        help_command: Union[commands.HelpCommand, None] = None
        tree_cls: type = discord.app_commands.CommandTree
        intents: discord.Intents = discord.Intents.default()
        intents.members = True
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

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def setup_hook(self) -> None:
        await startupPrint(self)


async def main():
    bot: commands.Bot = Builder()
    if LOAD_JISHAKU:
        await bot.load_extension("jishaku")

    extension_directories: List[PathLike] = COG_DIRECTORIES
    if LOAD_COGS_ON_STARTUP:
        await load_extensions(
            bot, extension_directories, spaces=20, ignore_errors=False, print_log=True
        )

    user = quote_plus(DB_USERNAME)
    password = quote_plus(DB_PASSWORD)

    # Connect to PostgreSQL database
    connection: asyncpg.connection.Connection = await asyncpg.connect(
        user=user, password=password
    )
    bot.apg = connection

    await ensureDB(connection, ensure_defaults=False)
    await formatCode()

    await bot.start(BOT_KEY)


if __name__ == "__main__":
    freeze_support()
    asyncio.run(main())
