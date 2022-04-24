from discord.app_commands import describe
from discord.ext import commands

import requests
import bs4


from _aux.embeds import fmte

class Utility(commands.Cog):
    """
    Helpful stuff
    """
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        pass

    def ge(self):
        return "🔢"

    @commands.hybrid_command()
    @describe(
        ephemeral = "Whether to publicly show the response to the command.",
    )
    async def ping(self, ctx: commands.Context, ephemeral: bool = False):
        """
        Returns the bot's latency, in milliseconds.
        """
        ping = self.bot.latency
        emt = "`🛑 [HIGH]`" if ping>0.4 else "`⚠ [MEDIUM]`"
        emt = emt if ping>0.2 else "`✅ [LOW]`"

        await ctx.send(embed=fmte(ctx, "🏓 Pong!", f"{round(ping*1000, 3)} miliseconds!\n{emt}"), ephemeral=ephemeral)
    
    @commands.hybrid_command()
    @describe(
        ephemeral = "Whether to publicly show the response to the command.",
    )
    async def bot(self, ctx: commands.Context, ephemeral: bool = False):
        """
        Returns information about the bot.
        """
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")
        embed = fmte(
            ctx,
            t = "Hello! I'm {}.".format(self.bot.user.name),
        )
        embed.add_field(
            name = "**__Statistics__**",
            value = "{s}**Creation Date:** <t:{}>{s}**Owners:** {}".format(
                round(self.bot.user.created_at.timestamp()),
                "\n{}".format(bb).join([str(c) for c in (await self.bot.application_info()).team.members]),
                s = b
            )
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)


    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(
        querey = "What to search for.",
        ephemeral = "Whether to publicly show the response to the command.",
    )
    async def search(self, ctx: commands.Context, querey: str, ephemeral: bool = False):
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
        embed = fmte(
            ctx,
            t = "Result found!",
        )
        await ctx.send("https://google.com{}".format(link), embed=embed, ephemeral=ephemeral)


async def setup(bot):
    await bot.add_cog(Utility(bot))