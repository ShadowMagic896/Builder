from _aux.userio import handle_error
from client_container import *
from discord.ext import tasks

class Watchers(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Client online [User: {self.bot.user}, ID: {self.bot.user.id}]")
        self.startup_SQL()
        self.apply_handers()
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        if message


    def startup_SQL(self):
        conn = sqlite3.connect("data/timers")
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
    
    def apply_handers(self):
        for cm in self.bot.commands:
            @cm.error
            async def gloal_handle(ctx, err):
                await handle_error(ctx, err)
                pass



async def setup(bot):
    await bot.add_cog(Watchers(bot))