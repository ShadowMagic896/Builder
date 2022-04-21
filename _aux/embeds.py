import discord
from datetime import datetime
from discord import Color as disco

def fmte(ctx = None, t = "", d = "", c = disco.teal(), u = None) -> discord.Embed:
    """
    Takes the sent information and returns an embed with a footer and timestamp added, with the default color being teal.
    """
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

def gge(self, ctx):
        return fmte(
            ctx,
            t = "**Command Group `{}`**".format(ctx.invoked_parents[0]),
            d = "**All Commands:**\n{}".format("".join(["ㅤㅤ`>>{} {} {}`\nㅤㅤ*{}*\n\n".format(
                ctx.invoked_parents[0] if len(ctx.invoked_parents) > 0 else "None", 
                c.name, 
                c.signature, 
                c.short_doc
            ) for c in getattr(self, ctx.invoked_parents[0]).commands]))
        )
