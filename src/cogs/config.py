from typing import Any

import asyncpg
from discord.app_commands import describe
from discord.ext import commands

from ..utils.abc import BaseCog
from ..utils.bot_abc import Builder, BuilderContext


class Config(BaseCog):
    """Change the bot's configuration"""

    def __init__(self, bot: Builder) -> None:
        self.cfdb = ConfigureDatabase(bot)
        super().__init__(bot)

    def ge(self) -> str:
        return "\N{GEAR}"

    @commands.hybrid_group()
    async def config(self, ctx: BuilderContext):
        pass

    @config.group(name="set")
    @commands.has_permissions(administrator=True)
    async def set_(self, ctx: BuilderContext):
        pass

    @set_.command(name="nsfw")
    @describe(toggle="New value for the setting")
    async def set_nsfw(self, ctx: BuilderContext, toggle: bool):
        """
        Whether to allow NSFW commands to be used in this server. Never allowed in non-nsfw channels
        """
        value = await self.cfdb.set_value(ctx.guild.id, "nsfw", str(toggle))
        await ctx.send(str(value))

    @config.group(name="get")
    async def get(self, ctx: BuilderContext):
        pass

    @get.command(name="nsfw")
    async def get_nsfw(self, ctx: BuilderContext):
        """
        Whether to allow NSFW commands to be used in this server. Never allowed in non-nsfw channels
        """
        value = await self.cfdb.get_value(ctx.guild.id, "nsfw")
        await ctx.send(str(value))


class ConfigureDatabase:
    def __init__(self, bot: Builder):
        self.bot = bot
        self.apg = bot.apg

    async def set_value(self, guild_id: int, key: str, value: str) -> asyncpg.Record:
        command = """
            INSERT INTO config
            VALUES (
                $1, $2, $3   
            )
            ON CONFLICT (gk_unique) DO UPDATE
                SET value=$3
                WHERE guild_id=$1 AND key=$2
            ON CONFLICT (g_unique) DO UPDATE
                SET key=$2, value=$3
                WHERE guildid=$1
            RETURNING *
        """
        return await self.apg.fetchrow(command, guild_id, key, value)

    async def get_value(self, guild_id: int, key: str) -> Any:
        command = """
            SELECT value
            FROM config
            WHERE guildid=$1 AND key=$2
        """
        return await self.apg.fetchrow(command, guild_id, key)


async def setup(bot: Builder):
    await bot.add_cog(Config(bot))
