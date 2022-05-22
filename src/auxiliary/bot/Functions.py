import asyncio
from asyncio.subprocess import PIPE, Process
from typing import List, Mapping, Tuple
import asyncpg
import chempy
from chempy.util import periodic

from data.ItemMaps import Chemistry


def fmtDict(d: dict):
    """
    Formats a dictionary to be placeable into a PostgreSQL DB.
    """
    return str(d).replace("'", '"')


async def ensureDB(
    connection: asyncpg.Connection, *, ensure_defaults=True, drop_all=False
):
    if drop_all:
        await connection.execute(
            """
            DROP TABLE IF EXISTS items CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
            DROP TABLE IF EXISTS inventories CASCADE;
            """
        )
    command: str = """
        CREATE TABLE IF NOT EXISTS items (
            itemid INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            userid BIGINT NOT NULL PRIMARY KEY,
            balance BIGINT DEFAULT 0 CHECK(balance >= 0)
        );
        
        CREATE TABLE IF NOT EXISTS inventories (
            userid BIGINT NOT NULL,
            itemid INTEGER NOT NULL,
            count INTEGER NOT NULL DEFAULT 0 CHECK(count >= 0),
            FOREIGN KEY (itemid) REFERENCES items (itemid) ON DELETE CASCADE,
            FOREIGN KEY (userid) REFERENCES users (userid) ON DELETE CASCADE,
            UNIQUE (userid, itemid)
        );
    """
    print("CREATING DATABASES...")
    await connection.execute(command)

    if ensure_defaults:
        print("ENSURING DEFAULT ITEMS...")
        command = """
            DELETE FROM items;
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
            INSERT INTO items
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
