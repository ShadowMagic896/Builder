from subprocess import Popen
from discord import app_commands
from discord.app_commands import describe
from discord.ext import commands

from typing import List
from data.settings import COG_DIRECTORIES

from src.auxiliary.user.Embeds import fmte
from src.auxiliary.bot.Extensions import load_extensions
from src.auxiliary.user.UserIO import explode


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_command()
    @commands.is_owner()
    @describe(params="The arguments to pass to Popen & autopep8")
    async def fmtcode(self, ctx, params: str = "-aaair"):
        """
        Formats the bot's code using autopep8
        """
        Popen(
            "py -m autopep8 %s R:\\VSCode-Projects\\Discord-Bots\\Builder" % params,
        ).stdout
        await ctx.send("Code formatting completed.")

    @commands.hybrid_command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: str = None):
        if spec:
            l: List[app_commands.AppCommand] = await self.bot.tree.sync(guild=ctx.guild)
        else:
            l: List[app_commands.AppCommand] = await self.bot.tree.sync()
        embed = fmte(ctx, t="%s Commands Synced" % len(explode(l)))
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context):
        await load_extensions(self.bot, COG_DIRECTORIES)
        await ctx.send("All Cogs Reloaded.")


async def setup(bot):
    await bot.add_cog(Dev(bot))
