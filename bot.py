import aiohttp
import asyncio
import asyncpg
import discord
import logging
import openai
import time

from multiprocessing import freeze_support
from discord.ext import commands
from typing import Any, Iterable, Union

from src.utils.startup_functions import (
    connect_database,
    do_prep,
    get_activity,
    startup_print,
)
from data.environ import APPLICATION_ID, BOT_KEY, OPENAI_KEY
from data.settings import PREFIXES

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
        application_id: str = APPLICATION_ID
        case_insensitive: bool = True

        super().__init__(
            command_prefix=command_prefix,
            help_command=help_command,
            tree_cls=tree_cls,
            intents=intents,
            application_id=application_id,
            case_insensitive=case_insensitive,
        )

        self.openai: openai = openai
        self.openai.api_key = OPENAI_KEY

        self.apg: asyncpg.Connection = None
        self.session: aiohttp.ClientSession = None
        self.start_unix: float = time.time()

        self.tree.fallback_to_global = True

    async def setup_hook(self) -> None:
        await startup_print(self)


class BuilderContext(commands.Context):
    def __init__(self, **data):
        self.bot: Builder = data["bot"]
        super().__init__(**data)


async def main():
    bot: Builder = Builder()
    async with aiohttp.ClientSession(
        headers={"User-Agent": "python-requests/2.27.1"}  # :troll:
    ) as bot.session:
        bot = await do_prep(bot)
        await bot.start(BOT_KEY)


if __name__ == "__main__":
    freeze_support()
    asyncio.run(main())
