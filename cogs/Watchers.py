from client_container import *
from discord.ext import tasks

class Watchers(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Client online [User: {self.bot.user}, ID: {self.bot.user.id}]")

        conn = sqlite3.connect("data/userdata")
        cur = conn.cursor()
        command = """
        CREATE TABLE IF NOT EXISTS 
        timers 
        (
            author_id INT, 
            start_time TEXT,
            current_time FLOAT
        )
        """
        cur.execute(command)
        conn.commit()
        conn.close()

async def setup(bot):
    await bot.add_cog(Watchers(bot))