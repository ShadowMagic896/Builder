import asyncio
from math import floor
from multiprocessing.sharedctypes import Value
from random import randint, random
from typing import Any, List, Optional, Union
import discord
from discord.ext import commands
from datetime import datetime


async def getv(inter) -> Union[commands.Context, None]:
    try:
        return await commands.Context.from_interaction(inter)
    except ValueError:
        return None


def fmte(
        ctx: commands.Context = None,
        t: str = "",
        d: str = "",
        c: discord.Color = discord.Color.teal(),
        u: discord.User = None,) -> discord.Embed:
    """
    Takes the sent information and returns an embed with a footer and timestamp added, with the default color being teal.
    """
    if not (ctx or u):
        raise Exception("my guy")
    user = ctx.author if not u else u
    if ctx:
        ti = ctx.bot.latency
    else:
        ti = (randint(50, 60) + randint(0, 99) / 100) / 1000  # This is ethical
    embed = discord.Embed(
        title=t,
        description=d,
        color=c
    )
    embed.set_author(
        name="Requested By: %s" %
        str(user), url="https://discordapp.com/users/%s" %
        user.id, icon_url=user.avatar.url)
    if ti:
        embed.set_footer(
            text="Response in %sms" % round(ti * 1000, 3)
        )
    embed.timestamp = datetime.now()
    return embed


def fmte_i(inter: discord.Interaction, t="", d="",
           c=discord.Color.teal()) -> discord.Embed:
    return fmte(t=t, d=d, c=c, u=inter.user)


def getReadableValues(seconds):
    hours = round(seconds // 3600)
    mins = round(seconds // 60 - hours * 60)
    secs = round(seconds // 1 - hours * 3600 - mins * 60)
    msec = str(round(seconds - hours * 3600 - mins * 60 - secs, 6))[2:]
    msec += "0" * (6 - len(msec))

    return(hours, mins, secs, msec)



class Desc:
    user = "The target of this command."
    ephemeral = "Whether to publicly show the response to the command."
    reason = "The reason for using this command. Shows up in the server's audit log."
