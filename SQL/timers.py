import sqlite3
import time
from typing import List, Tuple

from _aux.sql3OOP import Table


class Timer:
    def __init__(self) -> None:
        self.tab = Table("data/timers", "usertimers",
                         {"userid": "int", "startunix": "real"})

    def new_user(self, userid: int) -> None:
        self.tab.insert([userid, time.time()])
        self.tab.commit()

    def get_user_exists(self, userid: int):
        result = self.tab.select(conditions=[f"userid={userid}"]).fetchall()
        return len(result) != 0

    def get_user_time(self, userid: int):
        stime: List[Tuple[float]] = self.tab.select(
            values=["startunix"],
            conditions=[f"userid={userid}"]).fetchone()[0]
        return time.time() - stime

    def get_user_start(self, userid: int):
        return self.tab.select(values=["startunix"], conditions=[
                               f"userid={userid}"]).fetchone()[0]

    def delete_user(self, userid):
        self.tab.delete(conditions=[f"userid={userid}"])
        self.tab.commit()
