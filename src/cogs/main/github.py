import asyncio
from asyncio.subprocess import Process
import os
from pprint import pprint
import time
from urllib.parse import quote_plus
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

from aiohttp import ClientResponse
from bot import Builder, BuilderContext
from src.utils.constants import Const
from data.environ import LIBRARY_KEY
from src.utils.embeds import fmte

class GitHub(commands.Cog):
    def __init__(self, bot: Builder) -> None:
        self.bot=bot
        self.last_updated_log = 0
        super().__init__()
    
    def ge(self):
        return "\N{VideoCassette}"


    @commands.hybrid_group()
    async def github(self, ctx: BuilderContext):
        pass

    @github.command()
    async def user(self, ctx: BuilderContext, query: str):
        url: str = f"{Const.URLs.LIBRARY_API}/github/{query}"
        print(url)
        params = {"apikey": LIBRARY_KEY}
        response = await self.bot.session.get(url, params=params)
        json = await response.json()
        pprint(json)

    @github.command()
    async def builder(self, ctx: BuilderContext):
        """
        Gets the bot's GitHub push log
        """
        if time.time() - self.last_updated_log > 300:
            shell: Process = await asyncio.create_subprocess_shell(
                f"cd /d {os.getcwd()} && git config --global --add safe.directory R:/VSCode-Projects/Discord-Bots/Builder && git log -t --diff-merges=on --max-count 3 > data/logs/git.log"
            )
            await shell.communicate()
            self.last_updated_log = time.time()
        file: discord.File = discord.File(
            "data/logs/git.log",
            filename="repo.diff",
            description="Builder's GitHub repository log",
        )
        embed = fmte(
            ctx,
            t="Showing Git Log",
        )
        await ctx.send(embed=embed, file=file)
        file.close()


async def setup(bot: Builder):
    await bot.add_cog(GitHub(bot))