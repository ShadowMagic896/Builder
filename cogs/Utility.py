
import discord
from discord.ext import commands
from discord import app_commands, Interaction

import requests
import bs4
from typing import Literal


from _aux.embeds import fmte, fmte_i
from Help.TextHelp import EmbedHelp  

class Utility(commands.Cog):
    """
    Helpful stuff
    """
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        pass

    def ge(self):
        return "🔢"

    @app_commands.command()
    async def ping(self, inter: Interaction, ephemeral: bool = True):
        """
        Returns the bot's latency, in milliseconds.
        """
        ping = self.bot.latency
        emt = "`🛑 [HIGH]`" if ping>0.4 else "`⚠ [MEDIUM]`"
        emt = emt if ping>0.2 else "`✅ [LOW]`"

        await inter.response.send_message(embed=fmte_i(inter, "🏓 Pong!", f"{round(ping*1000, 3)} miliseconds!\n{emt}"), ephemeral=ephemeral)
    
    @app_commands.command()
    async def bot(self, inter: Interaction):
        """
        Returns information about the bot.
        """
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")
        embed = fmte_i(
            inter,
            t = "Hello! I'm {}.".format(self.bot.user.name),
            d = "Prefix: `<mention> or >>`"
        )
        embed.add_field(
            name = "**__Statistics__**",
            value = "{s}**Creation Date:** <t:{}>{s}**Owners:** {}".format(
                round(self.bot.user.created_at.timestamp()),
                "\n{}".format(bb).join([str(c) for c in (await self.bot.application_info()).team.members]),
                s = b
            )
        )
        await inter.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command()
    @commands.is_nsfw()
    async def search(self, inter: Interaction, querey: str, ephemeral: bool = True):
        """
        Searches the web for a website and returns the first result.
        """
        url = "https://www.google.com/search?q={}".format(querey)

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
        embed = fmte_i(
            inter,
            t = "Result found!",
            d = "*Bot is not responsible for results*"
        )
        await inter.response.send_message(link, embed=embed, ephemeral=ephemeral)


async def setup(bot):
    await bot.add_cog(Utility(bot))