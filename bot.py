from multiprocessing import freeze_support
import time
from typing import Iterable, Union
from urllib.parse import quote_plus
import aiohttp
import asyncpg
import discord
from discord.ext import commands

import asyncio
import logging

from src.utils.Extensions import load_extensions
from src.utils.Functions import (
    applyAllGlobalChecks,
    aquire_connection,
    formatCode,
    startupPrint,
)
from src.utils.Database import ensureDB
from src.utils.Stats import Stats
from data.Config import BOT_KEY
from data.Settings import (
    COG_DIRECTORIES,
    LOAD_COGS_ON_STARTUP,
    LOAD_JISHAKU,
    PREFIXES,
    SHOW_SOURCE_LINES,
    SOURCE_CODE_PATHS,
)
from src.utils.Docker import beginDocker

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

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.start_unix = time.time()

    async def setup_hook(self) -> None:
        await startupPrint(self)


async def main():
    bot: commands.Bot = Builder()
    if LOAD_JISHAKU:
        await bot.load_extension("jishaku")

    if LOAD_COGS_ON_STARTUP:
        await load_extensions(
            bot, COG_DIRECTORIES, spaces=20, ignore_errors=False, print_log=True
        )

    bot.apg = await aquire_connection()

    await ensureDB(bot)
    await formatCode()
    await beginDocker()

    await applyAllGlobalChecks(bot)

    await bot.start(BOT_KEY)


if __name__ == "__main__":
    freeze_support()
    asyncio.run(main())
