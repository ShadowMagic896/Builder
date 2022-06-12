import aiohttp
import asyncio
import asyncpg
import discord
import logging
import openai
import time

from multiprocessing import freeze_support
from discord.ext import commands
from typing import Iterable, Union

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
    SOURCE_CODE_PATHS,
    START_DOCKER_ON_STARTUP,
)
from src.utils.External import snekbox_exec

# Logging ---------------------------------------------------
logger: logging.Logger = logging.getLogger("discord")
logger.setLevel(logging.ERROR)

filename: str = "data\\logs\\_discord.log"
encoding: str = "UTF-8"
mode: str = "w"

handler: logging.FileHandler = logging.FileHandler(
    filename=filename, encoding=encoding, mode=mode
)
formatter: logging.Formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
)
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
        activity: discord.Activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{Stats.lineCount(SOURCE_CODE_PATHS)} LINES",
        )
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

        self.status: discord.Status = discord.Status("idle")
        self.openai: openai = openai
        self.openai.api_key = OPENAI_KEY

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.apg: asyncpg.Connection = None
        self.start_unix: float = time.time()

        self.tree.fallback_to_global = True

    async def setup_hook(self) -> None:
        await startupPrint(self)


class BuilderContext(commands.Context):
    def __init__(self, **data):
        self.bot: Builder = data["bot"]
        super().__init__(**data)


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
