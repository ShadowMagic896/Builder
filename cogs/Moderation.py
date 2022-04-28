from typing import Optional
import discord
from discord import app_commands
from discord.app_commands import describe, Range
from discord.ext import commands

import asyncio
import time as _time_
from datetime import datetime
import time
import pytz

from _aux.embeds import fmte
from _aux.userio import iototime, actual_purge


class Moderation(commands.Cog):
    """
    For keeping the users in line.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def ge(self):
        return "⚖️"

    @commands.hybrid_command()
    @describe(
        until="The time to automatically unlock the channel",
        reason="The reason for locking the channel. Show up on audit log.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, until: str = None, reason: str = "No reason given", ephemeral: bool = False):
        """
        Disallows non-admin users from sending messages in the channel where this was used.
        """
        embed = fmte(
            ctx,
            t="Channel Locked by {}.".format(
                ctx.author),
            d="Use `/unlock` to unlock it." if not until else "Until: <t:{}>".format(
                round(
                    time.time() +
                    iototime(until))))

        await ctx.send(embed=embed, ephemeral=ephemeral)

        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=False,
            add_reactions=False,
            reason=reason
        )

        if until:
            secs = iototime(until)
            await asyncio.sleep(secs)
            await ctx.channel.set_permissions(
                ctx.guild.default_role,
                send_messages=True,
                add_reactions=True,
                reason="Automatic Channel Unlock."
            )
            embed = fmte(
                ctx,
                t="Channel Unlocked",
                d="Channel originally locked by {}".format(ctx.author)
            )
            await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        reason="The reason for unlocking the channel. Shows up on audit log.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def unlock(self, ctx, reason: str = "No reason given", ephemeral: bool = False):
        """
        Manually unlocks a channel
        """
        embed = fmte(
            ctx,
            t="Channel Unlocked"
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=True,
            add_reactions=True,
            reason=reason
        )

    @commands.hybrid_command()
    @describe(
        user="The user to timeout.",
        time="The time to timeout for.",
        reason="The reason for timing out the user. Shows up on audit log.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, user: discord.Member, time: str = "15m", reason: str = "No reason given.", ephemeral: bool = False):
        """
        Times out a user.
        """
        st = _time_.time()

        if not time[0].isdigit():
            reason = "{} {}".format(time, reason)
            secs = 60 * 60
        else:
            secs = iototime(time)

        targtime = _time_.time() + secs
        until = datetime.fromtimestamp(
            targtime).astimezone(pytz.timezone("utc"))

        await user.timeout(until, reason=reason)
        embed = fmte(
            ctx,
            t="{} timed out.".format(user),
            d="**Until:** <t:{}>\n**Reason:** {}\n**Mod:** `{}`".format(
                round(until.timestamp()), reason, ctx.author)
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @commands.has_permissions(moderate_members=True)
    @describe(user="The user to untimeout",
              reason="The reason for untimingout the user. Shows up on the audit log.",
              ephemeral="Whether to publicly show the response to the command.",
    )
    async def untimeout(self, ctx: commands.Context, user: discord.Member, reason: str = "No reason given.", ephemeral: bool = False):
        """
        Removes the timeout from a user.
        """

        if not user.is_timed_out:
            embed = fmte(
                ctx,
                t="This user is not timed out."
            )
            await ctx.send(embed=embed, ephemeral=ephemeral)
            return

        at = user.timed_out_until
        # Set timeout value to right now
        await user.timeout(datetime.now(tz=pytz.timezone("utc")), reason=reason + " [Manual untimeout]")
        embed = fmte(
            ctx,
            t="{} is no longer timed out.".format(user),
            d="**Original timeout target:** <t:{}>\n**Reason:** {}\n**Mod:** `{}`".format(
                round(
                    at.timestamp()),
                reason,
                ctx.author))
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages = True)
    @describe(
        limit="Maximum number of messages to delete. This may not always be reached.",
        user="If specified, this will only delete messages by this user",
        reason="The reason for purging. Shows up on audit log.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def purge(self, ctx: commands.Context, limit: int, user: discord.Member = None, reason: str = "No reason given.", ephemeral: bool = False):
        """
        Purges a channel's messages.
        """
        if not user:
            r = await actual_purge(ctx, limit + 1)
            embed = fmte(
                ctx,
                t="{} Messages by All Users Deleted".format(r[0] - 1),
                d="Failed deletes: {}".format(r[1])
            )

        else:

            r = await actual_purge(ctx, limit + 1, user)
            embed = fmte(
                ctx,
                t="{} Messages by {} Deleted.".format(r[0] - 1, user),
                d="Failed deletes: {}.".format(r[1])
            )

        await ctx.send(embed=embed, ephemeral=ephemeral, delete_after=3)

    @commands.hybrid_command()
    @commands.has_permissions(manage_nicknames=True)
    @describe(
        user="The user to nickname. Defaults to the author.",
        name="The new name. Defaults to removing the nickname.",
        reason="The reason for renaming the user. Shows up on audit log.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def nick(self, ctx: commands.Context, user: discord.Member = None, name: str = None, reason: str = "No reason given.", ephemeral: bool = False):
        """
        Nicknames a user.
        """
        if not user:
            await ctx.author.edit(nick=name, reason=reason)
            embed = fmte(
                ctx,
                t="You have been renamed to {}."
            )
        else:
            await user.edit(nick=name, reason=reason)
            embed = fmte(
                ctx,
                t="{} has been renamed to {}".format(user, name)
            )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @commands.has_permissions(kick_members=True)
    @describe(
        user="The user to kick from the guild.",
        reason="The reason for kicking the member. Shows up on audit log.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def kick(self, ctx: commands.Context, user: discord.Member, reason: str = "No reason given.", ephemeral: bool = False):
        """
        Kicks a member from the guild. This user can be reinvited later.
        """

        await ctx.guild.kick(user, reason=reason)
        embed = fmte(
            ctx,
            t="`{}` kicked from `{}`".format(user, ctx.guild),
            d="Reason: `{}`".format(reason)
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @commands.has_permissions(ban_members = True)
    @describe(
        user = "The user to ban.",
        purgedays = "The amount of days' worth of messages to delete.",
        reason = "The reason for banning the user. Shows up in audit log.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def ban(self, ctx: commands.Context, user: discord.Member, purgedays: Range[int, 0, 7] = 0, reason: str = "No reason given", ephemeral: bool = False):
        """
        Bans a user from the server
        """
        await user.ban(delete_message_days=purgedays, reason=reason)
        embed = fmte(
            ctx,
            t = "%s Banned." % str(user),
            d = "**Reason:** {}\n**Days to purge:** {}".format(
                reason, purgedays
            )
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)
    
    @commands.hybrid_command()
    @commands.has_permissions(ban_members = True)
    @describe(
        user = "The user to unban.",
        reason = "The reason for unbanning the user. Shows up in audit log.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def unban(self, ctx: commands.Context, user: discord.User, reason: str = "No reason given", ephemeral: bool = False):
        """
        Unbans a user from the server
        """
        await user.unban(reason=reason)
        embed = fmte(
            ctx,
            t = "%s Unbanned." % str(user),
            d = "**Reason:** {}".format(
                reason
            )
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)



async def setup(bot):
    await bot.add_cog(Moderation(bot))
