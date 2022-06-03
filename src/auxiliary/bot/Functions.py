import asyncio
from asyncio.subprocess import PIPE, Process
import copy
from importlib import import_module
import importlib
import inspect
from os import PathLike, getcwd
import os
from typing import Callable, List, Literal, Mapping, Optional, Tuple, Type
import typing
import asyncpg
from chempy.util import periodic
import discord
from discord.ext import commands

from data.ItemMaps import Chemistry
from data.settings import STARTUP_ENSURE_DEFAULT_ATOMS, STARTUP_UPDATE_COMMANDS


def explode(l: List[commands.HybridCommand]):
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


async def ensureDB(
    bot: commands.Bot,
    connection: asyncpg.Connection,
    *,
    to_drop: List[str] = [],
):
    for tab in to_drop:
        await connection.execute(
            f"""
            DROP TABLE IF EXISTS {tab} CASCADE;
            """
        )
    command: str = """
        CREATE TABLE IF NOT EXISTS atoms (
            atomid INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            userid BIGINT NOT NULL PRIMARY KEY,
            balance BIGINT DEFAULT 0 CHECK (balance >= 0)
        );
        
        CREATE TABLE IF NOT EXISTS inventories (
            userid BIGINT NOT NULL,
            atomid INTEGER NOT NULL CHECK (atomid > 1),
            count INTEGER NOT NULL DEFAULT 0 CHECK (count > 0),
            FOREIGN KEY (atomid) REFERENCES atoms (atomid) ON DELETE CASCADE,
            FOREIGN KEY (userid) REFERENCES users (userid) ON DELETE CASCADE,
            UNIQUE (userid, atomid)
        );

        CREATE TABLE IF NOT EXISTS shops (
            identity SERIAL NOT NULL PRIMARY KEY,
            userid BIGINT NOT NULL,
            atomid INTEGER NOT NULL CHECK (atomid > 0),
            amount INTEGER NOT NULL CHECK (amount > 0),
            price BIGINT NOT NULL CHECK (price > 0),
            FOREIGN KEY (userid) REFERENCES users (userid) ON DELETE CASCADE,
            FOREIGN KEY (atomid) REFERENCES atoms (atomid) ON DELETE CASCADE,
            UNIQUE (userid, atomid)
        );

        CREATE TABLE IF NOT EXISTS disabled_commands (
            guildid BIGINT NOT NULL,
            commandname TEXT UNIQUE NOT NULL,
            FOREIGN KEY (commandname) REFERENCES commands (commandname) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS commands (
            commandname TEXT PRIMARY KEY,
            parents TEXT[]
        )
    """
    print("CREATING DATABASES...")
    await connection.execute(command)

    if STARTUP_ENSURE_DEFAULT_ATOMS:
        print("ENSURING DEFAULT ITEMS...")
        command = """
            DELETE FROM atoms;
        """
        await connection.execute(command)
        items: Mapping[str, (int, str)] = {
            name: (
                count + 1,
                f"With the symbol `{symbol}` and mass of `{mass}`, this element is number `{count+1}`",
            )
            for name, symbol, mass, count in [
                (
                    periodic.names[c],
                    periodic.symbols[c],
                    periodic.mass_from_composition({c + 1: 1}),
                    c,
                )
                for c in range(len(periodic.names))
            ]
        }
        arguments: List[Tuple[str, str]] = []
        for name, val in list(items.items()):
            arguments.append((val[0], name, val[1]))

        basecommand = """
            INSERT INTO atoms
            VALUES (
                $1,
                $2,
                $3
            )
        """
        await connection.executemany(basecommand, arguments)
    if STARTUP_UPDATE_COMMANDS:
        bot_commands = explode(bot.commands)
        arguments = [
            (
                command.qualified_name,
                [parent.qualified_name for parent in command.parents],
            )
            for command in bot_commands
        ]
        command = """
            DELETE FROM commands;
        """
        await connection.execute(command)
        command = """
            INSERT INTO commands
            VALUES (
                $1,
                $2
            )
        """
        await connection.executemany(command, arguments)


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


def interactionChoke(ctx: commands.Context):
    async def predicate():
        command = """
            SELECT commands
            FROM disabled_commands
            WHERE guildid = $1
        """
        result = await ctx.bot.apg.fetchrow(command, ctx.guild.id)
        print(result)
        if ctx.command.qualified_name in result:
            return False
        return True

    return commands.check(predicate)
