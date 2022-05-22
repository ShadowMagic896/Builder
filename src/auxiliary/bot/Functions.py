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
            atomid INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            price BIGINT NOT NULL,
            startnix BIGINT NOT NULL,
            endunix BIGINT NOT NULL,
            FOREIGN KEY (userid) REFERENCES users (userid) ON DELETE CASCADE,
            FOREIGN KEY (atomid) REFERENCES atoms (atomid) ON DELETE CASCADE,
            UNIQUE (userid, atomid),
            CHECK (
                amount > 0 AND 
                price > 0 AND 
                atomid > 0 AND 
                startunix < endunix
            )
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
