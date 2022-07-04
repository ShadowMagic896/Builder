import discord
from discord.app_commands import describe
from discord.ext import commands

from ..utils.bot_types import Builder, BuilderContext
from ..utils.subclass import BaseCog


class Config(BaseCog):
    def __init__(self, bot: Builder) -> None:
        self.cfdb = ConfigureDatabase(bot)
        super().__init__(bot)
    """Change the bot's configuration"""
    def ge(self) -> str:
        return "\N{GEAR}"
    
    @commands.hybrid_group()
    async def config(self, ctx: BuilderContext):
        pass

    @config.group()
    @commands.has_permissions(administrator=True)
    async def change(self, ctx: BuilderContext):
        pass

    @change.command()
    @describe(toggle="New value")
    async def nsfw(self, ctx: BuilderContext, toggle: bool):
        """
        Whether to allow NSFW commands to be used in this server. Never allowed in non-nsfw channels
        """
        value = await self.cfdb.set_value(ctx.guild.id, "nsfw", str(toggle))
        await ctx.send(str(value))

    @config.group()
    async def get(self, ctx: BuilderContext):
        pass

    @get.command()
    async def nsfw(self, ctx: BuilderContext):
        """
        Whether to allow NSFW commands to be used in this server. Never allowed in non-nsfw channels
        """
        value = await self.cfdb.get_value(ctx.guild.id, "nsfw")
        await ctx.send(str(value))


class ConfigureDatabase:
    def __init__(self, bot: Builder):
        self.bot = bot
        self.apg = bot.apg

    async def set_value(self, guild_id: int, key: str, value: str):
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

    async def get_value(self, guild_id: int, key: str):
        command = """
            SELECT value
            FROM config
            WHERE guildid=$1 AND key=$2
        """
        return await self.apg.fetchrow(command, guild_id, key)

async def setup(bot: Builder):
    await bot.add_cog(Config(bot))
