from typing import List, Mapping, Tuple

from chempy.util import periodic
from discord.ext import commands

from settings import STARTUP_ENSURE_DEFAULT_ATOMS, STARTUP_UPDATE_COMMANDS

from .functions import explode


async def ensure_db(
    bot: commands.Bot,
    *,
    to_drop: List[str] = [],
):
    for tab in to_drop:
        await bot.apg.execute(
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
        
        CREATE TABLE IF NOT EXISTS config (
            guildid BIGINT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            UNIQUE (guildid, key)
        )
    """
    await bot.apg.execute(command)

    if STARTUP_ENSURE_DEFAULT_ATOMS:
        command = """
            DELETE FROM atoms;
        """
        await bot.apg.execute(command)
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
        await bot.apg.executemany(basecommand, arguments)
    if STARTUP_UPDATE_COMMANDS:
        arguments = [
            (
                command.qualified_name,
                [parent.qualified_name for parent in command.parents],
            )
            for command in explode(bot.commands)
        ]
        command = """
            DELETE FROM commands;
        """
        await bot.apg.execute(command)
        command = """
            INSERT INTO commands
            VALUES (
                $1,
                $2
            )
        """
        await bot.apg.executemany(command, arguments)
