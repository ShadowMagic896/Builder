import discord
from discord import Color as disco

def fmte(ctx, t = "", d = "", c = disco.teal()) -> discord.Embed:
    embed = discord.Embed(
        title = t,
        description = d,
        color = c
    )
    embed.set_footer(text = f"Requested by {ctx.author}")
    return embed

def fmte_i(inter, t = "", d = "", c = disco.teal()) -> discord.Embed:
    embed = discord.Embed(
        title = t,
        description = d,
        color = c
    )
    embed.set_footer(text = f"Requested by {inter.user}")
    return embed