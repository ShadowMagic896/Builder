from client_container import *

class Utility(commands.Cog):
    """
    This cog is for any commands that help users find information about other users, this bot, the server, etc.
    """

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.command(name = "ping", description = "Returns the bot's latency, in milliseconds")
    async def ping(self, ctx):
        ping=self.bot.latency
        emt="`🛑 [HIGH]`" if ping>0.4 else "`⚠ [MEDIUM]`"
        emt=emt if ping>0.2 else "`✅ [LOW]`"

        await ctx.send(embed=fmte(ctx, "🏓 Pong!", f"{round(ping*1000, 3)} miliseconds!\n{emt}"))

async def setup(bot):
    await bot.add_cog(Utility(bot))