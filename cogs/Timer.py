from discord.app_commands import describe
from typing import List
import discord
from discord.ext import commands

from SQL.timers import Timer

import pytz
import time
from datetime import datetime
from _aux.embeds import fmte, getReadableValues


class Time(commands.Cog):
    """
    Don't have a clock? Now you do.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.tab = Timer()

    def ge(self):
        return "⌚"

    @commands.hybrid_command()
    @describe(
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def timer(self, ctx: commands.Context, ephemeral: bool = False):
        """
        Creates a new timer for the user, with the time starting at 00:00:00.00.
        """
        self.tab.delete_user(ctx.author.id)
        self.tab.new_user(ctx.author.id)
        embed = fmte(
            ctx=ctx,
            t="New timer made!",
            d="You can use `/check` to check your time, or `/stop` to delete your timer."
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        user="Whose timer to check",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def check(self, ctx: commands.Context, user: discord.Member = None, ephemeral: bool = False):
        """
        Checks the user's time. If no user is given, it used the author instead.
        """
        user = user if user else ctx.author
        if not self.tab.get_user_exists(user.id):
            raise commands.errors.BadArgument("This member has no timer.")

        else:
            seconds = self.tab.get_user_time(user.id)
            t = getReadableValues(seconds)

            h = str(t[0])
            m = str(t[1])
            s = str(t[2])
            d = str(t[3])

            formatted = "Time: `{}:{}:{}.{}`".format(
                "0" * (2 - len(h)) + h,
                "0" * (2 - len(m)) + m,
                "0" * (2 - len(s)) + s,
                d)
            extra = "```{} {}\n{} {}\n{} {}\n{} {}\n```\nTimer started: <t:{}>".format(
                    "0" * (2 - len(h)) + h, "hour" if h == "1" else "hours",
                    "0" * (2 - len(m)) +
                m, "minute" if m == "1" else "minutes",
                    "0" * (2 - len(s)) +
                s, "second" if s == "1" else "seconds",
                    d, "microseconds",
                    round(self.tab.get_user_start(user.id))
            )

            embed = fmte(
                ctx=ctx,
                t=formatted,
                d=extra
            )
            await ctx.send(embed=embed, ephemeral=ephemeral)

    def __check(self, user):
        seconds = self.tab.get_user_time(user.id)
        t = getReadableValues(seconds)
        h = str(t[0])
        m = str(t[1])
        s = str(t[2])
        d = str(t[3])

        formatted = "`{}:{}:{}.{}`".format(
            "0" * (2 - len(h)) + h,
            "0" * (2 - len(m)) + m,
            "0" * (2 - len(s)) + s,
            d)
        return formatted

    @commands.hybrid_command()
    @describe(
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def stop(self, ctx: commands.Context, ephemeral: bool = True):
        """
        Deletes the user's timer, allowing them to create a new one.
        """
        if not self.tab.get_user_exists(ctx.author.id):
            raise commands.errors.BadArgument("This member has no timer.")
        else:
            embed = fmte(
                ctx=ctx,
                t="Timer stopped at {}".format(self.__check(ctx.author)),
                d="You can use `/timer` to create a new one."
            )
            self.tab.delete_user(ctx.author.id)
            await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        zone="The timezone to get the time from.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def time(self, ctx: commands.Context, zone: str = "UTC", ephemeral: bool = True):
        """
        Gets the current time in the desired time zone.
        """
        lowered = [x.lower() for x in pytz.all_timezones]
        if not lowered.__contains__(zone.lower()):
            raise commands.errors.BadArgument(zone)
        else:
            time = pytz.timezone(zone)
            embed = fmte(
                ctx=ctx,
                t="Current datetime in zone {}:".format(time.zone),
                d="```{}```".format(datetime.now(pytz.timezone(zone)))
            )
            await ctx.send(embed=embed, ephemeral=ephemeral)

    @time.autocomplete("zone")
    async def time_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=zone, value=zone)
            for zone in pytz.all_timezones if current.lower() in zone.lower()
        ][:25]


async def setup(bot):
    await bot.add_cog(Time(bot))
