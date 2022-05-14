from subprocess import Popen
import discord
from discord import app_commands
from discord.app_commands import describe
from discord.ext import commands

from typing import Any, List, Literal, Mapping
from math import ceil

from src.auxiliary.user.Embeds import fmte, fmte_i
from src.auxiliary.user.UserIO import explode
from src.auxiliary.user.Converters import TimeConvert


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
    
    @commands.hybrid_command()
    @commands.is_owner()
    @describe(
        params="The arguments to pass to Popen & autopep8"
    )
    async def fmtcode(self, ctx, params: str = "-aaair"):
        """
        Formats the bot's code using autopep8
        """
        Popen(
            "py -m autopep8 %s R:\\VSCode-Projects\\Discord-Bots\\Builder" %
            params,).stdout
        await ctx.send("Code formatting completed.")

    @commands.hybrid_command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: str = None):
        if spec:
            l: List[app_commands.AppCommand] = await self.bot.tree.sync(guild=ctx.guild)
        else:
            l: List[app_commands.AppCommand] = await self.bot.tree.sync()
        embed = fmte(ctx, t="%s Commands Synced" %
                     len(explode(l)))
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def timetest(self, ctx: commands.Context, time: TimeConvert):
        await ctx.send(str(time))


async def setup(bot):
    await bot.add_cog(Dev(bot))