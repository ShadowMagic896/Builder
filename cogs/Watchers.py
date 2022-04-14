from client_container import *

class Watchers(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Client online [User: {self.bot.user}, ID: {self.bot.user.id}]")

async def setup(bot):
    await bot.add_cog(Watchers(bot))