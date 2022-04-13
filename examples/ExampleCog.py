from client_container import *

class ExampleCog(discord.ext.commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.command(aliases = ["anothername"])
    async def commandname(self, ctx):
        await ctx.send(f"{ctx.author} used {ctx.command.qualified_name}")

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))