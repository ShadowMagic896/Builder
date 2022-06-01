import asyncio
from asyncio.subprocess import PIPE, Process
from typing import Callable, List, Literal, Mapping, Optional, Tuple
import asyncpg
import chempy
from chempy.util import periodic
import discord
from discord.ext import commands

from data.ItemMaps import Chemistry


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


async def ensureDB(
    connection: asyncpg.Connection, *, ensure_defaults=False, to_drop: List[str] = []
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
            guildid BIGINT NOT NULL PRIMARY KEY,
            commands TEXT[]
        )
    """
    print("CREATING DATABASES...")
    await connection.execute(command)

    if ensure_defaults:
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
