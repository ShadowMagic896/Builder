import time

import asyncio
import discord
import os
from asyncio.subprocess import Process
from discord.ext import commands
from environ import LIBRARY_KEY
from src.utils.bot_types import Builder, BuilderContext
from src.utils.constants import URLs
from src.utils.embeds import format


class GitHub(commands.Cog):
    def __init__(self, bot: Builder) -> None:
        self.bot = bot
        self.last_updated_log = 0

    def ge(self):
        return "\N{VideoCassette}"

    @commands.hybrid_group()
    async def github(self, ctx: BuilderContext):
        pass

    @github.command()
    async def user(self, ctx: BuilderContext, query: str):
        url: str = f"{URLs.LIBRARY_API}/github/{query}"
        params = {"api_key": LIBRARY_KEY}
        response = await self.bot.session.get(url, params=params)
        json: dict = await response.json()
        if json.pop("error", None) is not None:
            raise commands.errors.BadArgument("Cannot find user")
        embed = await format(ctx, title=f"Information on: {query}")

        def at(x: str):
            parts = (
                str(x).replace("T", "-").replace(":", "-").removesuffix("Z").split("-")
            )
            parts = [float(x) for x in parts]
            mults = [31557600, 2629800, 86400, 3600, 60, 1]
            parts[0] -= 1970  # Unix begins at 1970, Jan 1 00:00:00.00 not 0
            result = sum(float(x) * mults[c] for c, x in enumerate(parts))
            return f"<t:{round(result)}:R>"

        embed.add_field(name="GitHub ID:", value=str(json["github_id"]))
        embed.add_field(name="Login:", value=str(json["login"]))
        embed.add_field(name="User Type:", value=str(json["user_type"]))
        embed.add_field(name="Creation:", value=at(json["created_at"]))
        embed.add_field(name="Last Updated:", value=at(json["updated_at"]))
        embed.add_field(name="Last Synced:", value=at(json["last_synced_at"]))
        embed.add_field(name="Name:", value=str(json["name"]))
        embed.add_field(name="Company:", value=str(json["company"]))
        embed.add_field(
            name="Blog:",
            value=f'[VIEW]({str(json["blog"])})' if json["blog"] else "None",
        )
        embed.add_field(name="Location:", value=str(json["location"]))
        embed.add_field(name="Hidden:", value=str(json["hidden"]))
        embed.add_field(name="Email:", value=str(json["email"]))
        embed.add_field(name="Bio:", value=str(json["bio"]))
        embed.add_field(name="UUID:", value=str(json["uuid"]))

        await ctx.send(embed=embed)

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
        embed = await format(
            ctx,
            title="Showing Git Log",
        )
        await ctx.send(embed=embed, file=file)
        file.close()


async def setup(bot: Builder):
    await bot.add_cog(GitHub(bot))
