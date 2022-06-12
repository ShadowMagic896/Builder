from importlib import reload
import importlib
import io
from os import listdir
import os
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
        log: str = ""
        to_reload = ["./src/utils"]
        to_reload.extend(COG_DIRECTORIES)
        for directory in to_reload:
            for file in os.listdir(directory):
                if os.path.isdir(f"{directory}/{file}"):
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
        await ctx.send(embed=embed)
        print("----------RELOADED----------")

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
