from email.mime import base
from typing import List
import discord
from discord.ext import commands

import os
import requests
import bs4
import slumber
import json
from bs4 import BeautifulSoup, ResultSet

from _aux.embeds import fmte


class Search(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.hybrid_group()
    async def search(self, ctx: commands.Context):
        """
        These commands are used to search the great big web for a variety of things.
        Neither this bot nor its owners or developers are responsible for any content returned.
        """
        embed = fmte(
            ctx,
            t = "**Command Group `{}`**".format(ctx.invoked_parents[0]),
            d = "**All Commands:**\n{}".format("".join(["ㅤㅤ`>>{} {} {}`\nㅤㅤ*{}*\n\n".format(
                ctx.invoked_parents[0] if len(ctx.invoked_parents) > 0 else "None", 
                c.name, 
                c.signature, 
                c.short_doc
            ) for c in getattr(self, ctx.invoked_parents[0]).commands]))
        )
        await ctx.send(embed = embed)
    
    @search.command(aliases = ["google", "internet", "querey"])
    async def web(self, ctx: commands.Context, *, querey: str):
        """
        Searches the web for a website and returns the first result.
        """
        if not ctx.channel.is_nsfw():
            embed = fmte(
                ctx,
                t = "This is not a NSFW channel.",
                d = "All commands of group `search` must be used in those channels!"
            )
            await ctx.send(embed = embed)
            return
        url = "https://www.google.com/search?q={}".format(" ".join(querey))

        res = requests.get(url)

        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        linkElements = soup.select("div#main > div > div > div > a")

        if len(linkElements) == 0:
            raise discord.NotFound("Could not find any valid link elements...")
        else:
            link = linkElements[0].get("href")
            i = 0
            while link[0:4] != "/url" or link[14:20] == "google":
                i += 1
                link = linkElements[i].get("href")
        embed = fmte(
            ctx,
            t = "Result found!",
            d = "*Bot is not responsible for results*"
        )
        await ctx.send(embed = embed)
        await ctx.send(link)










async def setup(bot):
    await bot.add_cog(Search(bot))