import discord
from discord.ext import commands

import asyncio
import time as _time_
from datetime import datetime
import pytz

from _aux.embeds import fmte
from _aux.userio import is_user, iototime, actual_purge

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.hybrid_command(aliases = ["mute", "m", "silence", "tm"])
    @commands.has_permissions(manage_messages = True)
    async def timeout(self, ctx: commands.Context, user: str, time: str = "15m", *, reason: str = "No reason given."):
        st = _time_.time()
        user = await is_user(ctx, user)
        if not user:
            embed = fmte(
                ctx, 
                t = "User not found.",
                d = "Please make sure you either input a user or a user's ID"
            )
            await ctx.send(embed=embed)
            return

        if not time[0].isdigit():
            reason = "{} {}".format(time, reason)
            secs = 60 * 60
        else:
            secs = iototime(time)

        targtime = _time_.time() + secs
        until = datetime.fromtimestamp(targtime).astimezone(pytz.timezone("utc"))
        try:
            await user.timeout(until, reason = reason)
            embed = fmte(
                ctx,
                t = "{} timed out.".format(user),
                d = "**Until:** <t:{}>\n**Reason:** {}\n**Mod:** `{}`".format(round(until.timestamp()), reason, ctx.author)
            )
            await ctx.send(embed = embed)
            await asyncio.sleep(secs-1)
            if user.is_timed_out:
                ...
            else:
                return
            embed = fmte(
                ctx,
                t = "{} is no longer timed out.".format(user),
                d = "**Timeout info:**\n**At:** <t:{}>\n**For:** `{}`\n**Until:** <t:{}>".format(
                    round(st),
                    time,
                    round(until.timestamp())
                )
            )
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            embed = fmte(
                ctx,
                t = "I do not have permission to timeout that user.",
                d = "Please make sure that I have the administrator role, and that you are not trying to timeout an admin!"
            )
            await ctx.send(embed = embed)
    
    @commands.hybrid_command(aliases = ["utm", "unmute"])
    @commands.has_permissions(manage_messages = True)
    async def untimeout(self, ctx: commands.Context, user: str, *, reason: str = "No reason given."):
        user = await is_user(ctx, user)
        if not user:
            embed = fmte(
                ctx, 
                t = "User not found.",
                d = "Please make sure you either input a user mention, a user's ID, a user's name, or a name#discriminator"
            )
            await ctx.send(embed=embed)
            return

        if not user.is_timed_out:
            embed = fmte(
                ctx,
                t = "This user is not timed out."
            )
            await ctx.send(embed=embed)
            return
        try:
            at = user.timed_out_until
            await user.timeout(datetime.now(tz = pytz.timezone("utc")), reason = reason + " [Manual untimeout]") # Set timeout value to right now
            print(datetime.fromtimestamp(_time_.time()).astimezone(pytz.timezone("utc")))
            embed = fmte(
                ctx,
                t = "{} is no longer timed out.".format(user),
                d = "**Original timeout target:** <t:{}>\n**Reason:** {}\n**Mod:** `{}`".format(round(at.timestamp()), reason, ctx.author)
            )
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            embed = fmte(
                ctx,
                t = "I do not have permission to untimeout that user.",
                d = "Please make sure that I have the administrator role!"
            )
            await ctx.send(embed=embed)
        
    @commands.hybrid_command(aliases = ["clean", "purgemessage"])
    async def purge(self, ctx: commands.Context, limit: int, user:str = "all"):
        if user == "all":
            r = await actual_purge(ctx, limit + 1)
            embed = fmte(
                ctx,
                t = "{} Messages by All Users Deleted".format(r[0]-1),
                d = "Failed deletes: {}".format(r[1])
            )
            await ctx.send(embed=embed, delete_after=3)
        else:
            _user = await is_user(ctx, user)
            if not _user:
                embed = fmte(
                    ctx,
                    t = "User {} not found.",
                    d = "Please make sure you either input a user mention, a user's ID, a user's name, or a name#discriminator."
                )
                await ctx.send(embed = embed)
                return
            r = await actual_purge(ctx, limit + 1, _user)
            embed = fmte(
                ctx,
                t = "{} Messages by {} Deleted.".format(r[0]-1, _user),
                d = "Failed deletes: {}.".format(r[1])
            )
            await ctx.send(embed=embed, delete_after=3)
        
    @commands.hybrid_command(aliases = ["rename", "nickname", "name"])
    @commands.has_permissions(change_nickname = True)
    async def nick(self, ctx: commands.Context, *, things: str = ""):
        things = things.split(" ")
        if len(things) == 0:
            await ctx.author.edit(nick="")
            return
        u = await is_user(ctx, things[0])
        if u:
            nick = " ".join(things[1:])
            bname = u.display_name
            if not ctx.author.guild_permissions.manage_nicknames and u != ctx.author:
                embed = fmte(
                    ctx,
                    t = "You do not have permission to change other people's nickname.",
                )
                await ctx.send(embed = embed)
                return
            await u.edit(nick = nick)
            embed = fmte(
                t = "{} renamed to {}".format(bname, u.display_name)
            )
            await ctx.send(embed = embed)
        else:
            if len(things) == 1:
                nick = things[0]
            else:
                nick = " ".join(things)
            await ctx.author.edit(nick = nick)


async def setup(bot):
    await bot.add_cog(Moderation(bot))

