import discord
from discord.ext import commands


from cogs.Currency import Currency

class Items(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
    
    @commands.hybrid_group()
    async def item(self, ctx: commands.Context):
        pass
    
async def setup(bot):
    await bot.add_cog(Items(bot))
    
