from discord.ext import commands

import sqlite3
import time
from datetime import datetime
import pytz


from _aux.userio import handle_error

class Watchers(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Client online [User: {self.bot.user}, ID: {self.bot.user.id}]")
        self.startup_SQL()
        self.apply_handers()
    
    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        mes = "Auth: {}; Com: {} [{}]; T: {}; Parents: {}; Children: {};\n".format(
            ctx.author,
            ctx.command,
            ctx.command_failed,
            datetime.now(tz = pytz.timezone("UTC")),
            ctx.invoked_parents,
            ctx.invoked_subcommand,
        )
        open("_commandlog.txt", "ab").write(mes.encode("UTF-8"))
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            data = "{} at {}: {}\n".format(message.author, datetime.fromtimestamp(time.time()), message.content)
            open("_dmlog.txt", "a").write(data)
        # await self.bot.process_commands(message) # This is no longer necessary in 2.0.0


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
            async def gloal_handle(self, ctx, err):
                await handle_error(ctx, err)
                pass



async def setup(bot):
    await bot.add_cog(Watchers(bot))