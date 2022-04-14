import discord
from datetime import datetime
from discord import Color as disco

def fmte(ctx = None, t = "", d = "", c = disco.teal(), u = None) -> discord.Embed:
    if not (ctx or u):
        raise Exception("my guy")
    embed = discord.Embed(
        title = t,
        description = d,
        color = c
    )
    embed.set_footer(text = f"Requested by {ctx.author}")
    embed.timestamp = datetime.now()
    return embed

def fmte_i(inter, t = "", d = "", c = disco.teal()) -> discord.Embed:
    embed = discord.Embed(
        title = t,
        description = d,
        color = c
    )
    embed.set_footer(text = f"Requested by {inter.user}")
    embed.timestamp = datetime.now()
    return embed

def getReadableValues(seconds):
    hours=round(seconds//3600)
    mins=round(seconds//60-hours*60)
    secs=round(seconds//1-hours*3600-mins*60)
    msec=str(round(seconds-hours*3600-mins*60-secs, 6))[2:]
    msec += "0"*(6-len(msec))
    
    return(hours, mins, secs, msec)
