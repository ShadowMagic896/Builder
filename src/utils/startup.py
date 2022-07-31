import asyncio
import logging
import os
import sys
import tkinter
import traceback
import warnings
from pathlib import Path
from types import FrameType
from typing import Any, Callable, Coroutine, Iterator, Tuple
from urllib.parse import quote_plus

import aiohttp
import asyncpg
import discord
import pytenno
import wavelink
from discord.ext import commands
from PIL import ImageFont
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from environ import DB_PASSWORD, DB_USERNAME
from settings import (GLOBAL_CHECKS, GLOBAL_COOLDOWN,
                      IGNORED_GLOBALLY_CHECKED_COMMANDS,
                      IGNORED_INHERITED_GROUP_CHECKS, INHERIT_GROUP_CHECKS,
                      LOAD_JISHAKU, LOGGING_LEVEL,
                      SOURCE_CODE_PATHS, START_DOCKER_ON_STARTUP)

from .bot_abc import Builder, ConfigureDatabase
from .coro import run
from .database import ensure_db
from .errors import Fatal
from .extensions import load_extensions
from .external import snekbox_exec
from .functions import explode
from .stats import Stats
from .types import Cache, Fonts

warnings.filterwarnings("error")


async def aquire_fonts() -> Fonts:
    return Fonts(bookosbi=ImageFont.FreeTypeFont(f"assets/fonts/bookosbi.ttf", size=20))


async def aquire_activity(bot: Builder) -> discord.Activity:

    activity: discord.Activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{Stats.line_count(SOURCE_CODE_PATHS)} LINES, {len([v for v in explode(bot.commands)])} COMMANDS",
    )
    return activity


async def aquire_driver(bot: Builder) -> webdriver.Chrome:
    executable_path = Path("assets/drivers/chromedriver.exe").absolute()
    binary_location: str = (
        "C:\\Program Files\\Google\\Chrome Beta\\Application\\chrome.exe"
    )

    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.headless = True

    if not os.path.exists(binary_location):
        raise Exception(
            "Google Chrome >= 103.x must be installed. Please see https://www.google.com/chrome/beta/"
        )
    options.binary_location = binary_location

    service = Service()
    service.path = executable_path

    driver: webdriver.Chrome = await run(
        webdriver.Chrome, options=options, service=service
    )
    driver.set_window_size(1920, 1080)
    bot.driver = driver


async def aquire_asyncpg(bot: Builder) -> None:
    user = quote_plus(DB_USERNAME)
    password = quote_plus(DB_PASSWORD)
    connection: asyncpg.connection.Connection = await asyncpg.connect(
        user=user, password=password
    )
    bot.apg = connection


async def aquire_caches(bot: Builder) -> Cache:
    bot.cache = Cache(
        RTFM={}, fonts=await aquire_fonts(), WFM_items=await aquire_items(bot)
    )


async def aquire_items(bot: Builder) -> list[str]:
    return [item.url_name for item in await bot.tenno.items.get_items(language="en")]


async def aquire_session(bot: Builder) -> aiohttp.ClientSession:
    bot.session = aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
        },
    )


async def aquire_tkroot(bot: Builder):
    bot.tkroot = tkinter.Tk()


async def aquire_cfdb(bot: Builder) -> None:
    bot.cfdb = ConfigureDatabase(bot)


async def apply_inherit_checks(bot: Builder) -> None:
    if not INHERIT_GROUP_CHECKS:
        return
    for group in [
        c for c in explode(bot.commands) if isinstance(c, commands.HybridGroup)
    ]:
        checks = group.checks
        for command in explode(group.commands):
            if command in IGNORED_INHERITED_GROUP_CHECKS:
                continue
            command.checks.extend(checks)


async def apply_to_global(bot: Builder, check: Callable[[Any], bool]) -> None:
    for command in explode(bot.commands):
        if command.qualified_name in IGNORED_GLOBALLY_CHECKED_COMMANDS:
            continue
        command.add_check(check)


async def apply_global_checks(bot: Builder) -> None:
    for check in GLOBAL_CHECKS:
        await apply_to_global(bot, check)


async def aquire_tenno(bot: Builder) -> None:
    bot.tenno = await pytenno.PyTenno().__aenter__()


async def prepare(bot: Builder) -> None:
    await bot.wait_until_ready()
    if LOAD_JISHAKU:
        await bot.load_extension("jishaku")
        logging.info("Cog Loaded: Jishaku")

    if START_DOCKER_ON_STARTUP:
        await snekbox_exec()
        logging.info("Snekbox Executed")

    await aquire_tenno(bot)
    logging.info("Tenno Aquired")

    await aquire_asyncpg(bot)
    logging.info("Database Aquired")

    await aquire_driver(bot)
    logging.info("Web Driver Aquired")

    await aquire_caches(bot)
    logging.info("Caches Aquired")

    await aquire_session(bot)
    logging.info("Session Aquired")

    await aquire_tkroot(bot)
    logging.info("Tkinter Root Aquired")

    await ensure_db(bot)
    logging.info("Databases Verified")

    await aquire_cfdb(bot)
    logging.info("Configuration Database Manager Aquired")

    await load_extensions(bot)
    logging.info("Startup Cogs Loaded")

    await add_global_cooldowns(bot)
    logging.info("Global Cooldown Added")

    await apply_global_checks(bot)
    logging.info("Global Checks Applied")

    # await apply_inherit_checks(bot)
    # logging.info("Inherit Checks Applied")

    logging.info("Startup Complete")


async def add_global_cooldowns(bot: Builder) -> None:
    for command in explode(bot.commands):
        command = commands.cooldown(*GLOBAL_COOLDOWN, commands.BucketType.user)(command)


def start(main: Coroutine) -> None:
    setup_logging()
    inital: bool = True
    last: str = ""
    last_error: Exception = ...
    while (
        inital
        or (
            last := input(
                f"\nENDED WITH FATAL ERROR: {last_error}\nRestart bot? (Y/N/V)\n  | "
            ).lower()
        )
        == "y"
    ):
        if inital:
            inital = not inital
        try:
            asyncio.run(main())
        except Fatal:
            logging.fatal("--- quitting ---")
            sys.exit()
        except Exception as err:
            last_error = err
    if last == "v":
        format_error_stack(traceback.walk_stack(None))
    sys.exit()


def format_error_stack(summary: Iterator[Tuple[FrameType, int]]):
    for frame, line in summary:
        msg: str = f"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Frame:
~~ {frame.f_code.co_filename}:{frame.f_lineno}
~~ {frame.f_code.co_name} [{frame.f_code.co_firstlineno} -> {frame.f_code.co_firstlineno+len([line for line in frame.f_code.co_lines()])}]
~~ {frame.f_lineno, line}
"""
        sys.stderr.write(msg)


def setup_logging() -> None:
    format: str = "%(name)s @ %(asctime)s !%(levelno)s: %(message)s"
    logging.basicConfig(level=LOGGING_LEVEL, format=format)
    logging.info("Logging Set Up")
    logger: logging.Logger = logging.getLogger("discord")
    logger.setLevel(logging.ERROR)

    filename: str = "logs\\discord.log"
    encoding: str = "UTF-8"
    mode: str = "w"

    handler: logging.FileHandler = logging.FileHandler(
        filename=filename, encoding=encoding, mode=mode
    )
    formatter: logging.Formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger: logging.Logger = logging.getLogger("matplotlib")
    logger.setLevel(logging.INFO)
    logger: logging.Logger = logging.getLogger("selenium")
    logger.setLevel(logging.INFO)
    logging.info("Discord Logging Set Up")
