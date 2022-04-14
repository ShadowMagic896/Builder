from math import floor
from pydoc import describe
import discord
from discord.ext import commands
import _aux

from _aux.embeds import fmte
from SQL.timers import Timer

class Utility(commands.Cog):
    """
    This cog is for any commands that help users find information about other users, this bot, the server, etc.
    """

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.hybrid_command(name = "ping")
    async def ping(self, ctx):
        """
        Returns the bot's latency, in milliseconds.
        Usage: >>ping
        """
        ping=self.bot.latency
        emt="`🛑 [HIGH]`" if ping>0.4 else "`⚠ [MEDIUM]`"
        emt=emt if ping>0.2 else "`✅ [LOW]`"

        await ctx.send(embed=fmte(ctx, "🏓 Pong!", f"{round(ping*1000, 3)} miliseconds!\n{emt}"))
    

    @commands.hybrid_group(name = "timer")
    async def timer(self, ctx):
        timer = Timer()
        if timer.get_user_exists(ctx.author.id):
            embed = fmte(
                ctx = ctx,
                t = "You have already initialized a timer.",
                d = "Maybe you meant `>>timer check`?",
            )
            await ctx.send(embed = embed)
        else:
            timer.new_user(ctx.author.id)
            embed = fmte(
                ctx = ctx,
                t = "Timer created!",
                d = "You can use `>>timer check` to check your time, or `>>timer clear` to delete your timer.",
            )
            await ctx.send(embed = embed)
    
    @timer.command()
    async def new(self, ctx):
        timer = Timer()
        if timer.get_user_exists(ctx.author.id):
            embed = fmte(
                ctx = ctx,
                t = "You have already initialized a timer.",
                d = "Maybe you meant `>>timer check`?",
            )
        else:
            timer.new_user(ctx.author.id)
            embed = fmte(
                ctx = ctx,
                t = "Timer created!",
                d = "You can use `>>timer check` to check your time, or `>>timer clear` to delete your timer.",
            )
        await ctx.send(embed = embed)
    
    @timer.command()
    async def check(self, ctx, user: discord.Member = None):
        _user = user if user else ctx.author
        timer = Timer()
        if not timer.get_user_exists(_user.id):
            embed = fmte(
                ctx = ctx,
                t = "You have not initialized a timer yet." if not user else "This user has no timer initialized.",
                d = "You can use `>>timer` to create one!" if not user else "They can do so by using `>>timer`!.",
            )
        else:
            timer.update_user(_user.id)
            seconds = timer.get_user_current(_user.id)

            embed = fmte(
                ctx = ctx,
                t = "Current timer value",
                d = _aux.embeds.makeReadable(seconds)
            )
        await ctx.send(embed=embed)
    
    @timer.command()
    async def clear(self, ctx):
        timer = Timer()
        if not timer.get_user_exists(ctx.author.id):
            embed = fmte(
                ctx = ctx,
                t = "You do not currently have any timer!",
                d = "You can create one with `>>timer` though!"
            )
        else:
            timer.delete_user(ctx.author.id)
            embed = fmte(
                ctx = ctx, 
                t = "Timer cleared!",
                d = "You can use `>>timer` to create a new one."
            )
        await ctx.send(embed=embed)
        
    


async def setup(bot):
    await bot.add_cog(Utility(bot))