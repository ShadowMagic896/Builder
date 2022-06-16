from typing import Any, Callable, Literal, Optional
from urllib.parse import quote_plus
import aiohttp
import asyncpg
import discord
from discord.ext import commands
from data.environ import DB_PASSWORD, DB_USERNAME

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from data.settings import (
    COG_DIRECTORIES,
    GLOBAL_CHECKS,
    IGNORED_GLOBALLY_CHECKED_COMMANDS,
    IGNORED_INHERITED_GROUP_CHECKS,
    INHERIT_GROUP_CHECKS,
    LOAD_COGS_ON_STARTUP,
    LOAD_JISHAKU,
    SOURCE_CODE_PATHS,
    START_DOCKER_ON_STARTUP,
)
from src.utils.extensions import load_extensions
from src.utils.external import snekbox_exec
from src.utils.functions import explode
from src.utils.stats import Stats
from src.utils.coro import run
from src.utils.types import Caches


def get_activity(bot: commands.Bot):

    activity: discord.Activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{Stats.line_count(SOURCE_CODE_PATHS)} LINES, {len(explode(bot.commands))} COMMANDS",
    )
    return activity


async def aquire_driver() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.headless = True
    driver: webdriver.Chrome = await run(webdriver.Chrome, options=options)
    driver.set_window_size(1920, 1080)
    return driver


async def do_prep(bot: commands.Bot) -> aiohttp.ClientSession:
    if LOAD_JISHAKU:
        await bot.load_extension("jishaku")

    if LOAD_COGS_ON_STARTUP:
        await load_extensions(
            bot, COG_DIRECTORIES, spaces=20, ignore_errors=False, print_log=False
        )


    if START_DOCKER_ON_STARTUP:
        await snekbox_exec()

    await apply_global_checks(bot)

    bot.apg = await aquire_db()
    bot.driver = await aquire_driver()
    bot.caches = aquire_caches()

    return bot


async def aquire_db():
    user = quote_plus(DB_USERNAME)
    password = quote_plus(DB_PASSWORD)
    connection: asyncpg.connection.Connection = await asyncpg.connect(
        user=user, password=password
    )
    return connection


def aquire_caches():
    return Caches(
        RTFM={}
    )


async def apply_inherit_checks(bot: commands.Bot):
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


async def apply_to_global(bot: commands.Bot, check: Callable[[Any], bool]):
    for command in explode(bot.commands):
        if command.qualified_name in IGNORED_GLOBALLY_CHECKED_COMMANDS:
            continue
        command.add_check(check)


async def apply_global_checks(bot: commands.Bot):
    for check in GLOBAL_CHECKS:
        await apply_to_global(bot, check)

async def startup_print(bot: commands.Bot):
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

    client: str = fmt("Client", bot.user)
    userid: str = fmt("User ID", bot.user.id)
    dpyver: str = fmt("Version", discord.__version__)

    bdr = "\n+-----------------------------------+\n"

    print(
        f"\n\t\N{WHITE HEAVY CHECK MARK} ONLINE{bdr}| {client}{bdr}| {userid}{bdr}| {dpyver}{bdr}"
    )

