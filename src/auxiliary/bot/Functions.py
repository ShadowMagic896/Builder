import asyncio
from asyncio.subprocess import PIPE, Process
import re
import asyncpg
import discord
from discord.ext import commands
from importlib import import_module
import inspect
from os import PathLike
import os
from typing import Callable, List, Literal, Optional
from urllib.parse import quote_plus

from data.Config import DB_PASSWORD, DB_USERNAME
from data.Settings import (
    GLOBAL_CHECKS,
    IGNORED_GLOBALLY_CHECKED_COMMANDS,
    IGNORED_INHERITED_GROUP_CHECKS,
    INHERIT_GROUP_CHECKS,
)


def explode(l: List[commands.HybridCommand]) -> List[commands.HybridCommand]:
    l = list(l)
    nl = []
    for c in l:
        if hasattr(c, "commands"):
            nl.extend(explode(c.commands))
        else:
            # if isinstance(c, commands.):
            #     continue # ignore text commands, just dev stuff
            nl.append(c)
    return nl


def fmtDict(d: dict):
    """
    Formats a dictionary to be placeable into a PostgreSQL DB.
    """
    return str(d).replace("'", '"')


async def addCogLoaders(bot: commands.Bot, paths: List[PathLike]):
    for dir_ in paths:
        if dir_.startswith("_"):
            continue
        for file in os.listdir(dir_):
            if file.startswith("_"):
                continue
            _formatted = file.replace("/", "\\")
            fullname = f"{dir_.replace('.', '')}\\{_formatted}".replace(
                "/", "."
            ).replace("\\", ".")
            await _addCogLoaders(bot, fullname)


async def _addCogLoaders(bot: commands.Bot, filename: PathLike):
    """
    Automatically adds all cog classes to the bot from a given file.
    """
    module = import_module(filename[1:-3])  # Remove the "." and ".py"
    cogs: List[commands.Cog] = []  # A list of all cog classes defined in the file

    # Get all classes in the file
    classes = inspect.getmembers(module, inspect.isclass)

    for name, class_ in classes:
        if discord.ext.commands.cog.Cog in class_.__mro__:
            print(f"Add class: {name}")
            cogs.append(class_)

    for cog in cogs:
        print(f"COG: {cog.qualified_name()}")
        await bot.add_cog(cog(bot))


async def formatCode():
    proc: Process = await asyncio.create_subprocess_shell(f"py -m black .", stdout=PIPE)
    await proc.communicate()


async def startupPrint(bot: commands.Bot):
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


async def enforceChecks(bot: commands.Bot):
    if INHERIT_GROUP_CHECKS:
        return
    for group in [
        c for c in explode(bot.commands) if isinstance(c, commands.HybridGroup)
    ]:
        checks = group.checks
        for command in explode(group.commands):
            if command in IGNORED_INHERITED_GROUP_CHECKS:
                continue
            command.checks.extend(checks)


async def applyGlobalCheck(
    bot: commands.Bot, check: Callable[[commands.Context], bool]
):
    for command in explode(bot.commands):
        if command.qualified_name in IGNORED_GLOBALLY_CHECKED_COMMANDS:
            continue
        command.add_check(check)


async def applyAllGlobalChecks(bot: commands.Bot):
    for check in GLOBAL_CHECKS:
        await applyGlobalCheck(bot, check)


async def aquireConnection():
    user = quote_plus(DB_USERNAME)
    password = quote_plus(DB_PASSWORD)
    connection: asyncpg.connection.Connection = await asyncpg.connect(
        user=user, password=password
    )
    return connection


async def urlFind(url: str):
    if not url.startswith("http"):
        url = f"https://{url}"
    regex = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    return regex.findall(url)
