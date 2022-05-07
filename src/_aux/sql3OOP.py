import sqlite3
from subprocess import Popen
from typing import Mapping, Type, List
from typing_extensions import Self

import os


class Table:
    def __init__(self,
                 database: str,
                 table: str,
                 values: Mapping[str,
                                 Type],
                 *,
                 if_not_exists: bool = True) -> None:
        """Creates a new table in `database` named `table` with `values`. Will throw an error if a table exists and `if_not_exists` is False"""
        self.con: sqlite3.Connection = sqlite3.connect(database=database)
        self.cur: sqlite3.Cursor = self.con.cursor()

        self.database = database
        self.table = table
        self.values = values

        ine: str = " IF NOT EXISTS" if if_not_exists else ""
        values: str = ", ".join(["{} {}".format(k, v)
                                for k, v in values.items()])

        command = """
            CREATE TABLE{}
            {} ({})
        """.format(
            ine,
            table,
            values
        )
        self.cur.execute(command,)

    def select(self, *, values: List[str] = "*",
               conditions: List[str] = {},
               orderby: str = "") -> sqlite3.Cursor:
        """Gets all `values` from all rows where all `conditions` are True. Retuns a `sqlite3.Cursor` for easier fetching."""
        values: str = ", ".join(values) if isinstance(values, List) else "*"
        where = "WHERE " if len(conditions) > 0 else ""
        orderby = "ORDER BY %s" % orderby if orderby else ""
        conditions: str = ", ".join(conditions)

        command = """
            SELECT {}
            FROM {}
            {}{}
            {}
        """.format(
            values,
            self.table,
            where,
            conditions,
            orderby
        )
        return self.cur.execute(command)

    def insert(self, values: List) -> Self:
        """Inserts `values` as a new row in the table"""
        values: str = ", ".join(["'{}'".format(c) for c in values])

        command = """
            INSERT INTO {}
            VALUES ({})
        """.format(
            self.table,
            values
        )
        self.cur.execute(command,)
        return self

    def update(self, values: List[str], *, conditions: List[str] = {}) -> Self:
        """Sets all values in the table to `values` whenever all `conditions` are True"""
        values: str = ", ".join(values)
        where = "WHERE " if len(conditions) > 0 else ""
        conditions: str = ", ".join(conditions)

        command = """
            UPDATE {}
            SET {}
            {}{}
        """.format(
            self.table,
            values,
            where,
            conditions
        )
        self.cur.execute(command)
        return self

    def delete(self, *, conditions: List[str]):
        conditions = ", ".join(conditions)
        command = """
            DELETE FROM {}
            WHERE {}
        """.format(self.table, conditions)
        self.cur.execute(command)

    def finish(self):
        """Shorthand for Table().commit() and Table().close()"""
        self.commit()
        self.close()

    def commit(self):
        """Commits changes to the database"""
        self.con.commit()

    def close(self):
        """Closes the database connection"""
        self.con.close()

    def drop(self):
        """Drops the working table"""
        self.cur.execute("DROP TABLE IF EXISTS {}".format(self.table))

    def kill(self):
        """Deletes the table's database"""
        os.remove(self.database)
