import discord
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
        self.bot: commands.Bot = bot
        pass

    def ge(self):
        return "🔢"
    
    @commands.hybrid_command()
    @describe(
        ephemeral = "Whether to publicly show the response to the command.",
    )
    async def invite(self, ctx: commands.Context, ephemeral: bool = False):
        """
        Gets a link to invite me to a server!
        """
        link = discord.utils.oauth_url(
            self.bot.application_id, 
            permissions = discord.Permissions(8), 
            scopes = ["applications.commands"],
            guild = ctx.guild,
        )
        embed = fmte(
            ctx,
            t = "Invite Me to a Server!",
            d = "[Invite Link]({})".format(link)
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

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
        user = "The user to get information on.",
        ephemeral = "Whether to publicly show the response to the command.",
    )
    async def info(self, ctx: commands.Context, user: discord.Member = None, ephemeral: bool = False):
        """
        Gets information about the user requested.
        """
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")

        user = user if user else ctx.author
        embed = fmte(
            ctx,
            t = "Information on {}".format(user)
        )
        embed.add_field(
            name = "***__General Info__***",
            value = "{s}**Name:** `{}`{s}**Nickname:** `{}`{s}**ID:** `{}`{s}**Nitro Since:** <t:{}>{}{s}".format(
                user, user.nick, user.id, round(user.premium_since.timestamp()) if user.premium_since else "`None`",
                s = b
            ),
            inline = False
        )
        embed.add_field(
            name = "***__Statistics__***",
            value = "{s}**Status:** `{}`{s}**Creation Date:** `<t:{}>`{s}**Join Date:** <t:{}>{s}**System User:** `{}`{s}".format(
                user.status, round(user.joined_at.timestamp()) if user.joined_at else "`Unknown`", round(user.created_at.timestamp()) if user.created_at else "`Unknown`", user.system,
                s = b
            )
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

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