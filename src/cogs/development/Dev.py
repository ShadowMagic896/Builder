import importlib
import io
import os
from subprocess import Popen
from discord import app_commands
import discord
from discord.app_commands import describe
from discord.ext import commands

from typing import List
from data.settings import COG_DIRECTORIES, DEVELOPMENT_GUILD_IDS, SOURCE_CODE_PATHS

from src.utils.embeds import fmte
from src.utils.functions import explode
from bot import BuilderContext
from src.utils.stats import Stats


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_command()
    @app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
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
        embed = fmte(ctx, t=f"Synced Commands {type_}", d=log or discord.utils.MISSING)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
    async def reload(self, ctx: BuilderContext):
        if ctx.interaction:
            await ctx.interaction.response.defer()
        log: str = ""
        to_reload = ["./src/utils"]
        to_reload.extend(COG_DIRECTORIES)
        for directory in to_reload:
            for file in os.listdir(directory):
                if os.path.isdir(f"{directory}/{file}"):  # Probably just pycaches
                    continue
                fp = f"{directory[2:].replace('/','.')}.{file[:-3]}"
                if fp in ctx.bot.extensions.keys():
                    log += f"**[EXT] {fp}**\n"
                    await ctx.bot.reload_extension(fp)
                else:
                    imp = importlib.import_module(fp)
                    importlib.reload(imp)
                    log += f"*{fp}* \n"

        embed = fmte(ctx, t="All Files Reloaded.", d=log)

        activity: discord.Activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{Stats.line_count(SOURCE_CODE_PATHS)} LINES, {len(explode(self.bot.commands))} COMMANDS",
        )
        await self.bot.change_presence(activity=activity, status="idle")
        await ctx.send(embed=embed)
        print("----------RELOADED----------")

    @commands.hybrid_command()
    @app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
    @commands.is_owner()
    async def embe(self, ctx: BuilderContext, code: str):
        file = discord.File(io.BytesIO(bytes(str(eval(code)), "UTF-8")), "untitled.txt")
        await ctx.send(file=file)


async def setup(bot):
    await bot.add_cog(Dev(bot))
