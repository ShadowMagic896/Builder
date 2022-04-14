import sqlite3
from datetime import datetime

class Timer:
    def __init__(self) -> None:
        self.con: sqlite3.Connection = sqlite3.connect("data/userdata")
        self.cur: sqlite3.Cursor = self.con.cursor()

    def new_user(self, user_id: int) -> None: # gonna kms
        command = """
            INSERT INTO timers
            VALUES (?, ?, ?)
        """
        self.cur.execute(command, (int(user_id), str(datetime.utcnow()), str(0)))
        self.con.commit()
    
    def get_user_start(self, user_id: int):
        command = """
            SELECT start_time
            FROM timers
            WHERE author_id = ?
        """
        result = self.cur.execute(command, (user_id,))
        self.con.commit()
        return result.fetchone()
    
    def get_user_exists(self, user_id: int):
        command = """
            SELECT *
            FROM timers
            WHERE author_id = ?
        """
        result = self.cur.execute(command, (user_id,)).fetchall()
        return user_id in [v[0] for v in result]

    def get_user_current(self, user_id: int):
        # command = """
        #     SELECT *
        #     FROM timers
        # """
        # result = self.cur.execute(command).fetchall()

        # print("ALL OWDMOWDM: {}".format(result))
        command = """
            SELECT *
            FROM timers
            WHERE author_id = ?
        """
        result = self.cur.execute(command, (user_id,)).fetchone()
        return round(result[2], 4)
    
    def update_user(self, user_id):
        command = """
            SELECT start_time
            FROM timers
            WHERE author_id = ?
        """

        result = self.cur.execute(command, (user_id,)).fetchone()
        new_time = (datetime.utcnow() - datetime.fromisoformat(result[0])).total_seconds()

        command = """
            UPDATE timers
            SET current_time = ?
            WHERE author_id = ?
        """
        self.cur.execute(command, (new_time, user_id,))
        self.con.commit()
    
    def delete_user(self, user_id):
        command = """
        DELETE
        FROM timers
        WHERE author_id = ?
        """

        self.cur.execute(command, (user_id,))
        self.con.commit()