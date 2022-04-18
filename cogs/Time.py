import discord
from discord.ext import commands

import pytz
from datetime import datetime

from SQL.timers import Timer

from _aux.embeds import fmte, getReadableValues

class Time(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(name = "timer")
    async def timer(self, ctx: commands.Context):
        embed = fmte(
            ctx,
            t = "**Command Group `{}`**".format(ctx.invoked_parents[0]),
            d = "**All Commands:**\n{}".format("".join(["ㅤㅤ`>>{} {} {}`\nㅤㅤ*{}*\n\n".format(
                ctx.invoked_parents[0], 
                c.name, 
                c.signature, 
                c.short_doc
            ) for c in getattr(self, ctx.invoked_parents[0]).commands]))
        )
        await ctx.send(embed = embed)
    
    @timer.command(aliases = ["restart"])
    async def new(self, ctx: commands.Context):
        """
        Creates a new timer for the user, with the time starting at 00:00:00.00.
        """
        timer = Timer()
        timer.delete_user(ctx.author.id)
        timer.new_user(ctx.author.id)
        embed = fmte(
            ctx = ctx,
            t = "New timer made!",
            d = "You can use `>>timer check` to check your time, or `>>timer del` to delete your timer."
        )
        await ctx.send(embed = embed)
    
    @timer.command()
    async def check(self, ctx: commands.Context, user: discord.Member = None):
        """
        Checks the user's time. If no user is given, it used the author instead.
        """
        _user = user if user else ctx.author
        timer = Timer()
        if not timer.get_user_exists(_user.id):
            embed = fmte(
                ctx = ctx,
                t = "You have not initialized a timer yet." if not user else "This user has no timer initialized.",
                d = "You can use `>>timer new` to create one!" if not user else "They can do so by using `>>timer new`!.",
            )
        else:
            timer.update_user(_user.id)
            seconds = timer.get_user_current(_user.id)
            t = getReadableValues(seconds)
            h = str(t[0])
            m = str(t[1])
            s = str(t[2])
            d = str(t[3])

            embed = fmte(
                ctx = ctx,
                t = "Time: `{}:{}:{}.{}`".format(
                    "0"*(2-len(h)) + h, 
                    "0"*(2-len(m)) + m, 
                    "0"*(2-len(s)) + s,
                    d),
                d = "```{} {}\n{} {}\n{} {}\n{} {}\n```".format(
                    "0"*(2-len(h)) + h, "hour" if h == "1" else "hours",
                    "0"*(2-len(m)) + m, "minute" if m == "1" else "minutes",
                    "0"*(2-len(s)) + s, "second" if s == "1" else "seconds", 
                    d, "microseconds"
                    )
            )
        await ctx.send(embed=embed)
    
    @timer.command(aliases = ["del", "d", "stop", "destroy"])
    async def clear(self, ctx: commands.Context):
        """
        Deletes the user's timer, allowing them to create a new one.
        """
        timer = Timer()
        if not timer.get_user_exists(ctx.author.id):
            embed = fmte(
                ctx = ctx,
                t = "You do not currently have any timer!",
                d = "You can create one with `>>timer new` though!"
            )
        else:
            timer.delete_user(ctx.author.id)
            embed = fmte(
                ctx = ctx, 
                t = "Timer stopped!",
                d = "You can use `>>timer new` to create a new one."
            )
        await ctx.send(embed=embed)
    
    # @commands.hybrid_command()
    # async def time(self, ctx: commands.Context, zone: str = "UTC"):
    #     lowered = [x.lower() for x in pytz.all_timezones]
    #     if not lowered.__contains__(zone.lower()):
    #         embed = fmte(
    #             ctx = ctx,
    #             t = "Sorry, I can't find that timezone."
    #         )
    #     else:
    #         time = pytz.timezone(zone)
    #         embed = fmte(
    #             ctx = ctx,
    #             t = "Current datetime in zone {}:".format(time.zone),
    #             d = "```{}```".format(datetime.now(pytz.timezone(zone)))
    #         )
    #     await ctx.send(embed=embed)
        

async def setup(bot):
    await bot.add_cog(Time(bot))