from typing import Any

import discord
from discord.app_commands import describe
from discord.ext import commands

import settings_config_default as default

from ..utils.abc import BaseCog
from ..utils.bot_abc import Builder, BuilderContext


class Config(BaseCog):
    """Change the bot's configuration"""

    def ge(self) -> str:
        return "\N{GEAR}"

    @commands.hybrid_group()
    async def config(self, ctx: BuilderContext):
        pass

    @config.group(name="set")
    async def set_(
        self,
        ctx: BuilderContext,
    ) -> None:
        pass

    @set_.command(name="prefix")
    @describe(prefix="The new prefix used to invoke text commands")
    @commands.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx: BuilderContext, prefix: str) -> None:
        """Set the guild's prefix for the bot"""
        await self.bot.cfdb.set_value(ctx.guild.id, "prefix", prefix)
        embed = await ctx.format(
            title="Prefix Changed",
            desc=f"New Prefix: `{prefix}`",
        )
        await ctx.send(embed=embed)

    @set_.command(name="nsfw")
    @describe(toggle="The new toggle for NSFW commands")
    @commands.has_permissions(manage_channels=True)
    async def set_nsfw(self, ctx: BuilderContext, toggle: bool) -> None:
        discord.Permissions().man
        """Whether to enable NSFW commands in the guild"""
        await self.bot.cfdb.set_value(ctx.guild.id, "nsfw", toggle)
        embed = await ctx.format(
            title="NSFW Changed",
            desc=f"New NSFW Toggle: `{toggle}`",
        )
        await ctx.send(embed=embed)

    @set_.command(name="colorroles")
    @describe(toggle="The new toggle for color roles")
    @commands.has_permissions(manage_roles=True)
    async def set_colorroles(self, ctx: BuilderContext, toggle: bool) -> None:
        """Whether to enable color roles in the guild"""
        await self.bot.cfdb.set_value(ctx.guild.id, "colorroles", toggle)
        embed = await ctx.format(
            title="Color Roles Changed",
            desc=f"New Color Roles Toggle: `{toggle}`",
        )
        await ctx.send(embed=embed)

    @config.group()
    async def get(self, ctx: BuilderContext) -> None:
        pass

    @get.command(name="prefix")
    async def get_prefix(self, ctx: BuilderContext) -> None:
        """Get the guild's prefix for the bot"""
        record: Any | None = await self.bot.cfdb.get_value(ctx.guild.id, "prefix")
        embed = await ctx.format(
            title="Prefix Retrieved",
            desc=f"Prefix: `{record['value'] if record is not None else default.PREFIX}`"
            + (f" [DEFAULT]" if record is None else ""),
        )
        await ctx.send(embed=embed)

    @get.command(name="nsfw")
    async def get_nsfw(self, ctx: BuilderContext) -> None:
        """Whether  NSFW commands are enabled in the guild"""
        record: Any | None = await self.bot.cfdb.get_value(
            ctx.guild.id, "nsfw"
        )  # values are converted to strings for the database, so we need to convert them back to booleans

        embed = await ctx.format(
            title="NSFW Retrieved",
            desc=f"NSFW Toggle: `{record['value'] if record is not None else default.NSFW}`"
            + (f" [DEFAULT]" if record is None else ""),
        )
        await ctx.send(embed=embed)

    @get.command(name="colorroles")
    async def get_colorroles(self, ctx: BuilderContext) -> None:
        """Whether color roles are enabled in the guild"""
        record: Any | None = await self.bot.cfdb.get_value(ctx.guild.id, "colorroles")
        embed = await ctx.format(
            title="Color Roles Retrieved",
            desc=f"Color Roles Toggle: `{record['value'] if record is not None else default.COLORROLES}`"
            + (f" [DEFAULT]" if record is None else ""),
        )
        await ctx.send(embed=embed)


async def setup(bot: Builder):
    await bot.add_cog(Config(bot))
