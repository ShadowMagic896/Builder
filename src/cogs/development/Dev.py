import io
from subprocess import Popen
from discord import app_commands
import discord
from discord.app_commands import describe
from discord.ext import commands

from typing import List
from data.Settings import COG_DIRECTORIES

from src.utils.Embeds import fmte
from src.utils.Extensions import load_extensions
from src.utils.Functions import explode
from bot import BuilderContext


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
    async def sync(self, ctx: BuilderContext, spec: str = None):
        if spec:
            l: List[app_commands.AppCommand] = await self.bot.tree.sync(guild=ctx.guild)
        else:
            l: List[app_commands.AppCommand] = await self.bot.tree.sync()
        embed = fmte(ctx, t="%s Commands Synced" % len(explode(l)))
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.is_owner()
    async def reload(self, ctx: BuilderContext):
        await load_extensions(self.bot, COG_DIRECTORIES, print_log=False)
        await ctx.send("All Cogs Reloaded.")

    @commands.hybrid_command()
    @commands.is_owner()
    async def embe(self, ctx: BuilderContext, code: str):
        file = discord.File(io.BytesIO(bytes(str(eval(code)), "UTF-8")), "untitled.txt")
        await ctx.send(file=file)

    @app_commands.command()
    async def testing(self, inter):
        print("Running testing")
        raise Exception


async def setup(bot):
    await bot.add_cog(Dev(bot))
