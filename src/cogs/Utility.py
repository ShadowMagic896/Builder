from datetime import datetime
import pytz
from auxiliary.Embeds import fmte
import math
import re
import time
import typing
import discord
from discord.app_commands import describe
from discord.ext import commands

import os
from typing import Any, List, Optional
from math import (radians, sin, cos, tan, asin, acos, atan, sinh, cosh, tanh)

import bs4
import numpy
import requests
import simpleeval
import warnings
warnings.filterwarnings("error")


class Utility(commands.Cog):
    """
    Helpful stuff
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self._last_result: Optional[Any] = None
        pass

    def ge(self):
        return "🔢"

    @commands.hybrid_command()
    @describe(
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def invite(self, ctx: commands.Context, ephemeral: bool = False):
        """
        Gets a link to invite me to a server!
        """
        link = discord.utils.oauth_url(
            self.bot.application_id,
            permissions=discord.Permissions(8),
            scopes=["bot", "applications.commands"],
            guild=ctx.guild,
        )
        embed = fmte(
            ctx,
            t="Invite Me to a Server!",
            d="[Invite Link]({})".format(link)
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def ping(self, ctx: commands.Context, ephemeral: bool = False):
        """
        Returns the bot's latency, in milliseconds.
        """
        ping = self.bot.latency
        emt = "`🛑 [HIGH]`" if ping > 0.4 else "`⚠ [MEDIUM]`"
        emt = emt if ping > 0.2 else "`✅ [LOW]`"

        await ctx.send(embed=fmte(ctx, "🏓 Pong!", f"{round(ping*1000, 3)} miliseconds!\n{emt}"), ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        user="The user to get information on.",
        ephemeral="Whether to publicly show the response to the command.",
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
            t="Information on {}".format(user)
        )
        embed.add_field(
            name="***__General Info__***",
            value="{s}**Name:** `{}`{s}**Nickname:** `{}`{s}**ID:** `{}`{s}**Nitro Since:** {}{s}".format(
                user,
                user.nick,
                user.id,
                ("t<:%s>" %
                 round(
                     user.premium_since.timestamp())) if user.premium_since else "`None`",
                s=b),
            inline=False)
        embed.add_field(
            name="***__Statistics__***",
            value="{s}**Status:** `{}`{s}**Creation Date:** <t:{}>{s}**Join Date:** <t:{}>{s}**System User:** `{}`{s}".format(
                user.status, round(
                    user.joined_at.timestamp()) if user.joined_at else "`Unknown`", round(
                    user.created_at.timestamp()) if user.created_at else "`Unknown`", user.system,
                s=b
            )
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def bot(self, ctx: commands.Context, ephemeral: bool = False):
        """
        Returns information about the bot.
        """
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")
        embed = fmte(
            ctx,
            t="Hello! I'm {}.".format(self.bot.user.name),
        )
        embed.add_field(
            name="**__Statistics__**",
            value="{s}**Creation Date:** <t:{}>{s}**Owners:** {}".format(
                round(self.bot.user.created_at.timestamp()),
                "\n{}".format(bb).join([str(c) for c in (await self.bot.application_info()).team.members]),
                s=b
            )
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(
        querey="What to search for.",
        ephemeral="Whether to publicly show the response to the command.",
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
            raise commands.errors.BadArgument(
                "Could not find any valid link elements...")
        else:
            link = linkElements[0].get("href")
            i = 0
            while link[0:4] != "/url" or link[14:20] == "google":
                i += 1
                link = linkElements[i].get("href")
        embed = fmte(
            ctx,
            t="Result found!",
        )
        await ctx.send("https://google.com{}".format(link), embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        objectid="The ID of the object to look for.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def find(self, ctx: commands.Context, objectid: int, ephemeral: bool = False):
        """
        Finds a user, role, custom emoji, sticker, channel, or server based on the ID given
        """
        found: Any = ...
        name: str = ...
        objtype: Any = ...
        attempts: List = [
            self.bot.get_user,
            ctx.guild.get_role,
            self.bot.get_emoji,
            self.bot.get_channel,
            self.bot.get_sticker,
            self.bot.get_guild,
        ]

        for t in attempts:
            if not (res := t(int(objectid))):
                continue

            found = res
            objtype = type(found)
            if isinstance(found, discord.User):
                name = str(found)
            else:
                name = res.name

            embed = fmte(
                ctx,
                t="Object Found!",
                d="**Name: ** %s\n**Type:** %s" %
                (name, objtype.__name__)
            )
            await ctx.send(embed=embed, ephemeral=ephemeral)
            return
        else:
            raise commands.errors.BadArgument(
                "Cannot find object: %s. Make sure this bot can see it. If it was an emoji, make sure it was not a default one." %
                str(objectid))

    @commands.hybrid_command()
    @describe(
        term="The term to search urbanDictionary for.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def urban(self, ctx: commands.Context, term: str, ephemeral: bool = False):
        """
        Searches the Urban Dictionary and returns the top results for a term
        """
        url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"

        params = {"term": term}

        headers = {
            "X-RapidAPI-Host": "mashape-community-urban-dictionary.p.rapidapi.com",
            "X-RapidAPI-Key": os.getenv("X_RAPID_API_KEY")}

        response = requests.request("GET", url, headers=headers, params=params)
        res = response.json()["list"]
        embed = fmte(ctx, t="`{}`: {} Definitions {}".format(
            term, len(res), "[Showing 5]" if len(res) > 5 else ""), )
        for d in res[:5]:
            embed.add_field(
                name="[{}]({})".format(
                    d["author"],
                    d["permalink"]),
                value="{}\n**Upvotes:** {}\n**Written On:** {}".format(
                    d["definition"],
                    d["thumbs_up"],
                    d["written_on"]),
                inline=False)

        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        term="The term to search urbanDictionary for.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def define(self, ctx: commands.Context, term: str, ephemeral: bool = False):
        """
        Searches Merriam-Webster's Collegiate dictionary and returns the top results for a term
        """
        response = requests.get(
            "https://dictionaryapi.com/api/v3/references/collegiate/json/{}?key={}".format(
                term.lower(), os.getenv("DICT_API_KEY"))).json()
        defs = []
        dates = []
        types = []

        for defi in response:
            defs.append(("".join(defi["shortdef"][0])).capitalize())
            dates.append(defi["date"])
            types.append(defi["fl"])

        embed = fmte(
            ctx,
            t="Definition(s) for the word: {} [{}]".format(
                term.capitalize(),
                len(defs)
            ),
        )
        if len(defs) < 1:
            raise ValueError('Word not found/no definition')

        cut = None if len(defs) <= 5 else len(defs) - 5
        defs = defs[:5]

        for c, item in enumerate(defs):
            embed.add_field(
                name="Definition {}, {}: *`[{}]`*".format(
                    c + 1,
                    types[c].capitalize(),
                    str(dates[c])[:dates[c].index("{")] if "{" in str(
                        dates[c]) else str(dates[c])
                ),
                value=item,
                inline=False
            )
        if cut:
            embed.add_field(
                name="...and %s more definitions." %
                cut,
                value="-------------------------------------------------------------------",
                inline=False)
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    async def math(self, ctx: commands.Context, equation: str, ephemeral: bool = False):
        """
        Evaluates a simple mathematical expression. Supports operators, trig funcs, Numpy, and typing.
        """
        st = time.time()
        res = simpleeval.SimpleEval(
            functions=self.newOps(), names=self.newNames(
                ctx, False)).eval(equation)
        embed = fmte(
            ctx,
            t=res,
            d="Solved in `%sms`" % round((time.time() - st) * 1000, 5)
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    async def eval(self, ctx: commands.Context):
        await ctx.interaction.response.send_modal(CodeModal(ctx))

    def newOps(self):
        f = simpleeval.DEFAULT_FUNCTIONS
        f.update({
            "sin": lambda n: sin(radians(n)),
            "cos": lambda n: cos(radians(n)),
            "tan": lambda n: tan(radians(n)),
            "asin": lambda n: asin(radians(n)),
            "acos": lambda n: acos(radians(n)),
            "atan": lambda n: atan(radians(n)),
            "sinh": lambda n: sinh(radians(n)),
            "cosh": lambda n: cosh(radians(n)),
            "tanh": lambda n: tanh(radians(n)),
            "root": lambda n, b: n ** (1 / b),
            "round": lambda n, b: round(n, b)})
        return f
    
    @commands.hybrid_command()
    @describe(
        zone="The timezone to get the time from.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def time(self, ctx: commands.Context, zone: str = "UTC", ephemeral: bool = False):
        """
        Gets the current time in the desired time zone.
        """
        lowered = [x.lower() for x in pytz.all_timezones]
        if not lowered.__contains__(zone.lower()):
            raise commands.errors.BadArgument(zone)
        else:
            time = pytz.timezone(zone)
            embed = fmte(
                ctx=ctx,
                t="Current datetime in zone {}:".format(time.zone),
                d="```{}```".format(datetime.now(pytz.timezone(zone)))
            )
            await ctx.send(embed=embed, ephemeral=ephemeral)

    @time.autocomplete("zone")
    async def time_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=zone, value=zone)
            for zone in pytz.all_timezones if current.lower() in zone.lower()
        ][:25]

    def newNames(self, ctx: commands.Context, expanded: bool):
        f = simpleeval.DEFAULT_NAMES
        f.update((key, getattr(typing, key))
                 for key in dir(typing) if not key.startswith("_"))
        f.update(
            {
                "numpy": numpy,
                "discord": discord
            }
        )
        if expanded:
            f.update(
                {
                    "discord": discord,
                    "math": math,
                    "re": re,
                    "time": time,
                }
            )
        return f


class CodeModal(discord.ui.Modal):
    def __init__(self, ctx) -> None:
        self.ctx: commands.Context = ctx
        super().__init__(title="Code Evaluation")
    code = discord.ui.TextInput(
        label="Please paste / type code here",
        style=discord.TextStyle.long
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        estart = time.time()
        inst = Utility(self.ctx.bot)
        value = self.code.value.replace("^", "**")
        try:
            result = simpleeval.SimpleEval(
                functions=inst.newOps(), names=inst.newNames(
                    self.ctx, True)).eval(value)
            self.err = None
        except (simpleeval.AssignmentAttempted, simpleeval.FeatureNotAvailable) as err:
            self.err = err
            result = "ERROR OCCURRED"

        embed = fmte(
            self.ctx,
            t=result,
            d="```py\n%s\n#Computed in %sms```\n**WARNINGS:** ```%s```" %
            (value,
             (time.time() -
              estart) /
                1000,
                self.err or "No warnings detected!"),
            c=discord.Color.teal() if self.err else None)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
