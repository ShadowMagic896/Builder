from typing import Optional

import discord
import numpy as np
from discord.ext import commands
from PIL import Image

import settings_config_default as default

from ..utils.abc import BaseCog
from ..utils.bot_abc import Builder, BuilderContext
from ..utils.converters import RGB
from ..utils.coro import run


class ColorRoles(BaseCog):
    def colorroles_config_check():
        print("Checking for colorroles_config...")

        @commands.check
        async def predicate(ctx: BuilderContext) -> bool:
            value = await ctx.bot.cfdb.get_value(ctx.guild.id, "colorroles")
            if value is None:  # Config not set, assume default
                return default.COLOR_ROLES
            return bool(value)

        return predicate

    @commands.hybrid_group()
    async def colorroles(self, ctx: BuilderContext):
        pass

    @colorroles.command(name="set")
    async def set_(self, ctx: BuilderContext, color: RGB(alpha=False)):
        """Creates a new color role with the specified color, or updates an existing one"""
        rbg = tuple(int(t) for t in color)
        if (
            existing := discord.utils.get(ctx.author.roles, name=ctx.author.name)
        ) is not None:
            await existing.edit(color=discord.Color.from_rgb(*rbg))
            embed = await ctx.format(
                title="Color Role Updated",
                desc=f"New Color: `{color}`",
            )
            await ctx.send(embed=embed)
        else:
            role = await ctx.guild.create_role(
                reason="Custom Color Role",
                name=ctx.author.name,
                permissions=ctx.guild.default_role.permissions,
                color=discord.Color.from_rgb(*rbg),
            )
            await ctx.author.add_roles(role)
            embed = await ctx.format(
                title="Color Role Created",
                desc=f"Color: `{color}`",
            )

    @colorroles.command()
    @colorroles_config_check()
    async def dominant(self, ctx: BuilderContext):
        """Creates a new role, or updates an existing one, with the dominant color of your avatar"""
        img: Image.Image = await run(
            Image.frombytes,
            "RGB",
            (128, 128),
            (await ctx.author.display_avatar.read()),
        )
        colors = img.getcolors(maxcolors=2**24)
        colors.sort(key=lambda c: c[0], reverse=True)
        dominant: tuple[int, int, int] = colors[0][1]

        if (
            existing := discord.utils.get(ctx.author.roles, name=ctx.author.name)
        ) is not None:
            await existing.edit(color=discord.Color.from_rgb(*dominant))
            embed = await ctx.format(
                title="Color Role Updated",
                desc=f"New Color: `{np.array(dominant)}`",
            )
        else:
            role = await ctx.guild.create_role(
                reason="Custom Color Role",
                name=ctx.author.name,
                permissions=ctx.guild.default_role.permissions,
                color=discord.Color.from_rgb(*dominant),
            )
            await ctx.author.add_roles(role)
            embed = await ctx.format(
                title="Color Role Created",
                desc=f"Color: `{np.array(dominant)}`",
            )
        await ctx.send(embed=embed)

    @colorroles.command()
    async def remove(self, ctx: BuilderContext):
        """Removes your custom color role"""
        if (
            existing := discord.utils.get(ctx.author.roles, name=ctx.author.name)
        ) is None:
            raise ValueError("You do not have a custom color role!")
        await existing.delete()
        embed = await ctx.format(
            title="Color Role Removed",
        )
        await ctx.send(embed=embed)


async def setup(bot: Builder):
    await bot.add_cog(ColorRoles(bot))
