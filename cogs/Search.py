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
    
    def ge(self):
        return "🌐"
    
    @commands.hybrid_command(aliases = ["google", "internet", "querey", "query"])
    @commands.is_nsfw()
    async def search(self, ctx: commands.Context, *, querey: str):
        """
        Searches the web for a website and returns the first result.
        """
        url = "https://www.google.com/search?q={}".format(" ".join(querey))

        res = requests.get(url)

        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        linkElements = soup.select("div#main > div > div > div > a")

        if len(linkElements) == 0:
            raise commands.errors.BadArgument("Could not find any valid link elements...")
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