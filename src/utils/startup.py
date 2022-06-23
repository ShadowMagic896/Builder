import asyncio
import logging
import warnings
from multiprocessing import freeze_support
import os
from pathlib import Path
import sys
from typing import Any, Callable, Literal, Optional
from urllib.parse import quote_plus
import aiohttp
import asyncpg
import discord
from discord.ext import commands
from environ import BOT_KEY, DB_PASSWORD, DB_USERNAME
from PIL import ImageFont

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from settings import (
    EXT_DIRECTORIES,
    GLOBAL_CHECKS,
    IGNORED_GLOBALLY_CHECKED_COMMANDS,
    IGNORED_INHERITED_GROUP_CHECKS,
    INHERIT_GROUP_CHECKS,
    LOAD_COGS_ON_STARTUP,
    LOAD_JISHAKU,
    LOGGING_LEVEL,
    SOURCE_CODE_PATHS,
    START_DOCKER_ON_STARTUP,
)
from src.utils.extensions import load_extensions
from src.utils.external import snekbox_exec
from src.utils.functions import explode
from src.utils.stats import Stats
from src.utils.coro import run
from src.utils.types import Cache, Fonts
from src.utils.bot_types import Builder
from src.utils.errors import Fatal

warnings.filterwarnings("error")
async def aquire_fonts() -> Fonts:
    return Fonts(
        bookosbi = ImageFont.FreeTypeFont(f"assets/fonts/bookosbi.ttf", size=20)
    )

async def aquire_activity(bot: commands.Bot) -> discord.Activity:

    activity: discord.Activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{Stats.line_count(SOURCE_CODE_PATHS)} LINES, {len([v for v in explode(bot.commands)])} COMMANDS",
    )
    return activity


async def aquire_driver() -> webdriver.Chrome:
    executable_path = Path("assets/drivers/chromedriver.exe").absolute()
    binary_location: str ="C:\\Program Files\\Google\\Chrome Beta\\Application\\chrome.exe"

    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.headless = True

    if not os.path.exists(binary_location):
        raise Exception("Google Chrome >= 103.x must be installed. Please see https://www.google.com/chrome/beta/")
    options.binary_location = binary_location
    
    service = Service()
    service.path = executable_path

    driver: webdriver.Chrome = await run(webdriver.Chrome, options=options, service=service)
    driver.set_window_size(1920, 1080)
    return driver


async def aquire_db() -> asyncpg.Connection:
    user = quote_plus(DB_USERNAME)
    password = quote_plus(DB_PASSWORD)
    connection: asyncpg.connection.Connection = await asyncpg.connect(
        user=user, password=password
    )
    return connection


async def aquire_caches() -> Cache:
    return Cache(
        RTFM={},
        fonts=await aquire_fonts()
    )

async def aquire_connection() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
        },
    )


async def apply_inherit_checks(bot: commands.Bot) -> None:
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


async def apply_to_global(bot: commands.Bot, check: Callable[[Any], bool]) -> None:
    for command in explode(bot.commands):
        if command.qualified_name in IGNORED_GLOBALLY_CHECKED_COMMANDS:
            continue
        command.add_check(check)


async def apply_global_checks(bot: commands.Bot) -> None:
    for check in GLOBAL_CHECKS:
        await apply_to_global(bot, check)


async def prepare(bot: commands.Bot) -> commands.Bot:
    if LOAD_JISHAKU:
        await bot.load_extension("jishaku")
        logging.info("Cog Loaded: Jishaku")

    if LOAD_COGS_ON_STARTUP:
        await load_extensions(
            bot, EXT_DIRECTORIES, spaces=20, ignore_errors=False, print_log=False
        )
        logging.info("Startup Cogs Loaded")

    if START_DOCKER_ON_STARTUP:
        await snekbox_exec()
        logging.info("Snekbox Executed")

    await apply_global_checks(bot)
    logging.info("Global Checks Applied")
    await apply_inherit_checks(bot)
    logging.info("Inherit Checks Applied")

    bot.apg = await aquire_db()
    logging.info("Database Aquired")
    bot.driver = await aquire_driver()
    logging.info("Web Driver Aquired")
    bot.caches = await aquire_caches()
    logging.info("Caches Aquired")
    bot.session = await aquire_connection()
    logging.info("Session Aquired")
    return bot


def start(main: Callable) -> None:
    freeze_support()
    setup_logging()
    inital: bool = True
    last_error: Exception = ...
    while inital or input(f"\nENDED WITH FATAL ERROR: {last_error}\nRestart bot? (Y/N)\n  | ").lower() == "y":
        if inital:
            inital = not inital
        try:
            asyncio.run(main())
        except Fatal:
            logging.fatal("--- quitting ---")
            sys.exit()
        except Exception as err:
            last_error = err
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

def boot() -> None:
    async def main():
        bot: Builder = Builder()
        bot: Builder = await prepare(bot)
        try:
            await bot.start(BOT_KEY)
        except aiohttp.ClientConnectionError as err:
            logging.fatal("Could not locate host")
            await bot.session.close()
            raise Fatal("Cannot locate host") from err
    start(main)