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
    if not user:
        return None
    if user.startswith("<@"):
        try:
            _id = int(str(user)[2:-1])
        except ValueError:
            return None
    else:
        try:
            _id = int(user)
        except ValueError:
            return None
    try:
        user = await ctx.guild.fetch_member(_id)
        return user
    except discord.errors.NotFound:
        return None

async def handle_error(ctx: commands.Context, error: commands.errors.CommandInvokeError):
    embed = fmte(
        ctx,
        t = "An Error Occurred!",
        d = "**Error:** {}\n".format(
            error.original,
        ),
        c = discord.Color.red(),
    )
    await ctx.send(embed=embed)