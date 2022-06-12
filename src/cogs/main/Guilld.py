import asyncio
from copy import copy
from typing import Optional
import discord
from discord.app_commands import describe
from discord.ext import commands

from src.utils.Embeds import fmte
from bot import BuilderContext


class Guild(commands.Cog):
    """
    Get them in line
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def ge(self):
        return "\N{HUT}"

    @commands.hybrid_group()
    @commands.guild_only()
    async def guild(self, ctx: BuilderContext):
        pass

    @guild.group()
    async def channel(self, ctx: BuilderContext):
        pass

    @channel.command()
    @commands.has_permissions(manage_channels=True)
    @describe(
        name="What to rename the channel to",
        reason="Why to rename the channel. Shows up on audit log",
        channel="The channel to rename",
    )
    async def rename(
        self,
        ctx: BuilderContext,
        name: str,
        reason: Optional[str] = "No reason given",
        channel: discord.TextChannel = commands.parameter(
            default=lambda c: c.channel, displayed_default=lambda c: c.channel.name
        ),
    ):
        """
        Renames a channel
        """
        oldchan = copy(channel)
        chan = await channel.edit(name=name, reason=reason)
        embed = fmte(ctx, t="Channel Renamed")
        embed.add_field(name="Previous Name", value=oldchan.name, inline=False)
        embed.add_field(name="New Name", value=chan.name, inline=False)

        await ctx.send(embed=embed)

    @channel.command()
    @commands.has_permissions(manage_channels=True)
    @describe(
        reason="Why to nuke the channel. Shows up on the audit log",
        channel="The channel to nuke",
    )
    async def nuke(
        self,
        ctx: BuilderContext,
        reason: Optional[str] = "No reason provided",
        channel: discord.TextChannel = commands.parameter(
            default=lambda c: c.channel, displayed_default=lambda c: c.channel.name
        ),
    ):
        """
        Deletes and recreates an identical channel, essentially deleting all messages from that channel
        """
        newchan = await ctx.guild.create_text_channel(
            name=channel.name,
            reason="Channel Recreated After Nuking",
            category=channel.category,
            news=channel.is_news(),
            position=channel.position,
            topic=channel.topic,
            slowmode_delay=channel.slowmode_delay,
            nsfw=channel.nsfw,
            overwrites=channel.overwrites,
            default_auto_archive_duration=channel.default_auto_archive_duration,
        )
        await channel.delete(reason=reason)

        embed = fmte(ctx, t="Channel Nuked!")
        embed.add_field(name="Reason:", value=reason)
        await asyncio.sleep(0.25)
        await newchan.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Guild(bot))