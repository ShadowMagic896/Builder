import io
from subprocess import Popen
from typing import List

import discord
from discord import app_commands
from discord.app_commands import describe
from discord.ext import commands

from settings import DEVELOPMENT_GUILD_IDS, SOURCE_CODE_PATHS

from ..utils.abc import BaseCog
from ..utils.bot_abc import Builder, BuilderContext
from ..utils.extensions import extend_dir
from ..utils.functions import explode
from ..utils.stats import Stats


class Dev(BaseCog):
    @commands.hybrid_command()
    @app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
    @commands.is_owner()
    @describe(params="The arguments to pass to Popen & autopep8")
    async def fmtcode(self, ctx: BuilderContext, params: str = "-aaair"):
        """
        Formats the bot's code using autopep8
        """
        Popen(
            "py -m autopep8 %s R:\\VSCode-Projects\\Discord-Bots\\Builder" % params,
        ).stdout
        await ctx.send("Code formatting completed.")

    @commands.hybrid_command()
    @app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
    @app_commands.rename(glob="global")
    async def sync(self, ctx: BuilderContext, glob: bool = False):
        """
        Sync global commands to discord
        """
        type_ = "Globally" if glob else f"Within {len(DEVELOPMENT_GUILD_IDS)} Guilds"
        log: str = ""
        if glob:
            cmds = await self.bot.tree.sync()
            log += f"**~ GLOBAL:** {len(cmds)} BASE"
        else:
            for guild in DEVELOPMENT_GUILD_IDS:
                cmds = await ctx.bot.tree.sync(guild=discord.Object(guild))
                log += f"**~ GUILD {guild}:** {len(cmds)} BASE"
        embed = await ctx.format(
            title=f"Synced Commands {type_}", desc=log or discord.utils.MISSING
        )
        await ctx.send(embed=embed)
        print(f"--- {'g' if glob else 'l'}_sync ---")

    @commands.hybrid_command()
    @app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
    async def reload(self, ctx: BuilderContext):
        log: str = await self.bot.reload_source()

        embed = await ctx.format(title="All Files Reloaded.", desc=log)

        activity: discord.Activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{Stats.line_count(extend_dir('./src'))} LINES, {len([v for v in explode(self.bot.commands)])} COMMANDS",
        )
        await self.bot.change_presence(activity=activity, status="idle")
        await ctx.send(embed=embed)
        print("--- reload ---")

    @commands.hybrid_command()
    @app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
    @commands.is_owner()
    async def embe(self, ctx: BuilderContext, code: str):
        file = discord.File(io.BytesIO(bytes(str(eval(code)), "UTF-8")), "untitled.txt")
        await ctx.send(file=file)


async def setup(bot):
    await bot.add_cog(Dev(bot))
