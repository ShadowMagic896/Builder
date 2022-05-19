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
import pymongo
from pymongo.server_api import ServerApi
import logging

from src.auxiliary.bot.Extensions import load_extensions
from src.auxiliary.bot.Stats import Stats
from data.config import Config

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
        command_prefix: List[str] = when_mentioned_or("dev>>")
        help_command: Union[commands.HelpCommand, None] = None
        tree_cls: type = discord.app_commands.CommandTree
        intents: discord.Intents = discord.Intents.default()
        intents.members = True

        activity: discord.Activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{Stats.lineCount(['./data', './src'])} LINES",
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
        status: str = "idle"
        self.status = discord.Status(status)
        self.tree.fallback_to_global = False

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def setup_hook(self) -> None:
        _fmt: Callable[[str, Optional[int], Optional[Literal["before", "after"]]]] = (
            lambda value, size=25, style="before": str(value)
            + " " * (size - len(str(value)))
            if style == "after"
            else " " * (size - len(str(value))) + str(value)
        )
        fmt: Callable[
            [str, str, Optional[int], Optional[int]]
        ] = lambda name, value, buf1=10, buf2=22: "%s: %s|" % (
            _fmt(name, buf1, "after"),
            _fmt(value, buf2, "after"),
        )

        client: str = fmt("Client", self.user)
        userid: str = fmt("User ID", self.user.id)
        dpyver: str = fmt("Version", discord.__version__)

        bdr = "\n+-----------------------------------+\n"

        print(
            f"\n\t\N{WHITE HEAVY CHECK MARK} ONLINE{bdr}| {client}{bdr}| {userid}{bdr}| {dpyver}{bdr}"
        )

        proc: Process = await asyncio.create_subprocess_shell(
            f"py -m black .", stdout=PIPE
        )
        await proc.communicate()


async def main():
    bot: commands.Bot = Builder()
    await bot.load_extension("jishaku")
    extension_directories: List[PathLike] = [
        "./src/cogs/development",
        "./src/cogs/economy",
        "./src/cogs/main",
    ]
    await load_extensions(
        bot, extension_directories, spaces=20, ignore_errors=False, print_log=True
    )

    user = quote_plus(Config().DB_USERNAME)
    password = quote_plus(Config().DB_PASSWORD)

    command: str = """
        CREATE TABLE IF NOT EXISTS users
        (userid INT PRIMARY KEY, balance INT, items JSON)
    """

    # Connect to PostgreSQL database
    connection: asyncpg.connection.Connection = await asyncpg.connect(
        user=user, password=password
    )
    await connection.execute(command)

    bot.apg = connection
    await bot.start(Config().BOT_KEY)


if __name__ == "__main__":
    freeze_support()
    asyncio.run(main())
