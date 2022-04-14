import discord
from discord import Color as disco

def fmte(ctx = None, t = "", d = "", c = disco.teal(), u = None) -> discord.Embed:
    if ctx is None and u is None:
        raise Exception("my guy")
    embed = discord.Embed(
        title = t,
        description = d,
        color = c
    )
    embed.set_footer(text = f"Requested by {ctx.author if not u else u}")
    return embed

def fmte_i(inter, t = "", d = "", c = disco.teal()) -> discord.Embed:
    embed = discord.Embed(
        title = t,
        description = d,
        color = c
    )
    embed.set_footer(text = f"Requested by {inter.user}")
    return embed

def makeReadable(seconds):
    hours=seconds//3600
    mins=seconds//60-hours*60
    secs=seconds//1-hours*3600-mins*60
    msec=seconds-hours*3600-mins*60-secs
    
    # hours=hours if len(str(hours))==2 else f"0{hours}"
    # mins=mins if len(str(mins))==2 else f"0{mins}"
    # secs=secs if len(str(secs))==2 else f"0{secs}"
    
    return f"{round(hours)}:{round(mins)}:{round(secs)}.{str(round(msec, 5))[2:]}"
