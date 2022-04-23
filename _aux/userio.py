from inspect import trace
from multiprocessing.sharedctypes import Value
from types import coroutine
import discord
from discord.ext import commands
from _aux.embeds import fmte
import traceback
import sys

def iototime(userinput: str):
    seconds = 0
    t = userinput
    def e(l: list):
        for r in l:
            if t.endswith(r):
                return True
        return False

    def findLimit(input):
        for c, char in enumerate(t):
            try: int(char)
            except: break
        return int(c)

    if any([e(["s","sec", "secs", "second", "seconds"])]):
        return int(t[:findLimit(t)])

    elif any([e(["m", "min", "mins", "minute", "minutes"])]):
        return int(t[:findLimit(t)]) * 60
        
    elif any([e(["h", "hr", "hrs", "hour", "hours"])]):
        return int(t[:findLimit(t)]) * 60 * 60

    elif any([e(["d", "ds", "day", "days"])]):
        return int(t[:findLimit(t)]) * 60 * 60 * 24

    elif any([e(["w", "wk", "wks", "week", "weeks"])]):
        return int(t[:findLimit(t)]) * 60 * 60 * 24 * 7
    
    else:
        return 60 * 60 # Not sure what they meant, so just do an hour.

async def is_user(ctx: commands.Context, user: str = None) -> discord.Member | None:
    r = ""
    if not user:
        r =  None
    _id = None
    if user.startswith("<@"): # User is a mention
        try:
            _id = int(str(user)[2:-1])
        except ValueError:
            r =  None
    else: # It is a user ID
        try:
            _id = int(user) # Just an ID
        except ValueError:
            for m in ctx.guild.members: # Try to catch a name
                if m.name == user or "{}#{}".format(m.name, m.discriminator) == user:
                    _id = m.id
            else:
                r =  None
    try:
        user = await ctx.guild.fetch_member(_id)
        return user
    except discord.errors.NotFound:
        r = None
    
    if not r:
        raise commands.errors.MemberNotFound(user)


async def actual_purge(ctx: commands.Context, limit, user: discord.Member = None):
    errors = 0
    dels = 0
    async for m in ctx.channel.history(limit = round((limit + 10) * 1.5)):
        if (m.author == user if user else True): # if there is a user, care, otherwise just go on ahead
            try:
                await m.delete()
            except discord.errors.Forbidden or discord.errors.NotFound:
                errors += 1
            dels += 1
        if dels == limit:
            break
    return (dels, errors)