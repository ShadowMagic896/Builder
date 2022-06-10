import aiohttp
from datetime import datetime
import io
from textwrap import indent
import pytz
from data.Settings import EVALUATION_TRUNCATION_THRESHOLD
import time

import discord
from discord.app_commands import describe
from discord.ext import commands

from typing import Any, List, Tuple
from data import Config
import bs4
import requests
import warnings
from src.utils.Embeds import fmte
from src.utils.Subclass import BaseModal
from src.utils.Converters import TimeConvert
from src.utils.Errors import *

warnings.filterwarnings("error")


class Utility(commands.Cog):
    """
    Helpful stuff
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.container_users: List[int] = []
        self.jobs: List[int] = []
        pass

    def ge(self):
        return "\N{INPUT SYMBOL FOR NUMBERS}"

    @commands.hybrid_command()
    @describe()
    async def ping(self, ctx: commands.Context):
        """
        Returns the bot's latency, in several regards.
        """

        def getSym(sec: float, target: float, leniency: float = 0.25):
            lnt: float = target * leniency
            if sec < target:
                return "\N{WHITE HEAVY CHECK MARK} LOW"
            # print(
            #     f"Ping: {sec}\nTarg: {target}\nDiff: {abs(target - sec)}\nLeni: {lnt}\n"
            # )
            return (
                "\N{OCTAGONAL SIGN} HIGH"
                if abs(target - sec) > lnt
                else "\N{WARNING SIGN} MEDIUM"
                if abs(target - sec) > lnt / 1.5
                else "\N{WHITE HEAVY CHECK MARK} LOW"
            )

        results: List[Tuple[str, Tuple[float, str]]] = []
        expected = [0.05, 0.0015, 0.175]
        botlat = self.bot.latency
        results.append(
            ("\N{Shinto Shrine} Gateway Latency", (botlat, getSym(botlat, expected[0])))
        )

        st = time.time()
        await self.bot.apg.execute("SELECT 1")
        end = time.time() - st
        results.append(
            ("\N{Floppy Disk} Database Latency", (end, getSym(end, expected[1])))
        )

        st = time.time()
        await self.bot.session.get("https://www.google.com")
        end = time.time() - st
        results.append(
            (
                "\N{Globe with Meridians} AioHTTP Latency [Google]",
                (end, getSym(end, expected[2])),
            )
        )

        # print(results)
        embed = fmte(ctx, t="\N{Table Tennis Paddle and Ball} Pong!")
        for c, res in enumerate(results):
            embed.add_field(
                name=f"**{res[0]}**",
                value=f"```ansi\n\u001b[0;34m{round(res[1][0] * 1000, 5)}ms\n{res[1][1]}\n\u001b[1;37mExpected: {expected[c]*1000}ms\n```",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @describe(
        user="The user to get information on.",
    )
    async def info(self, ctx: commands.Context, user: discord.Member = None):
        """
        Gets information about the user requested.
        """
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")

        user = user if user else ctx.author
        embed = fmte(ctx, t="Information on {}".format(user))
        made = (
            round(user.created_at.timestamp())
            if user.created_at is not None
            else "`Unknown`"
        )
        joined = (
            round(user.joined_at.timestamp())
            if user.joined_at is not None
            else "`Unknown`"
        )
        prem = (
            round(user.premium_since.timestamp())
            if user.premium_since is not None
            else "`None`"
        )

        embed.add_field(
            name="***__General Info__***",
            value=f"**Name:** `{user}`{b}**Nickname:** `{user.nick}`{b}**ID:** `{user.id}`{b}**Nitro Since:** {prem}{b}",
            inline=False,
        )
        embed.add_field(
            name="***__Statistics__***",
            value=f"{b}**Status:** `{user.status}`\n**Creation Date:** <t:{made}>{b}**Join Date:** <t:{joined}>{b}**System User:** `{user.system}`",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @describe()
    async def bot(self, ctx: commands.Context):
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
                "\n{}".format(bb).join(
                    [str(c) for c in (await self.bot.application_info()).team.members]
                ),
                s=b,
            ),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(
        query="What to search for.",
    )
    async def search(self, ctx: commands.Context, query: str):
        """
        Searches the web for a website and returns the first result.
        """
        url = "https://www.google.com/search?q={}".format(query)

        res = requests.get(url)

        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        linkElements = soup.select("div#main > div > div > div > a")

        if len(linkElements) == 0:
            raise commands.errors.BadArgument(
                "Could not find any valid link elements..."
            )
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
        await ctx.send("https://google.com{}".format(link), embed=embed)

    @commands.hybrid_command()
    @describe(
        objectid="The ID of the object to look for.",
    )
    async def find(self, ctx: commands.Context, objectid: str):
        """
        Finds a Member, Role, Channel, Message, Custom Emoji, Sticker, Server, or User from its ID.
        """
        objectid = int(objectid)
        found: Any = ...
        name: str = ...
        objtype: Any = ...
        attempts: List = [
            ctx.guild.get_member,
            ctx.guild.get_role,
            ctx.guild.get_channel,
            ctx.channel.get_partial_message,
            self.bot.get_emoji,
            self.bot.get_sticker,
            self.bot.get_guild,
            self.bot.get_user,
        ]
        for t in attempts:
            if not (found := t(objectid)):
                continue

            objtype = type(found).__name__
            name = str(found)

            if isinstance(found, discord.PartialMessage):
                name = found.jump_url

            embed = fmte(
                ctx,
                t="Object Found!",
            )
            embed.add_field(
                name="NAME",
                value=name,
            )
            embed.add_field(name="TYPE", value=objtype)
            return await ctx.send(embed=embed)
        else:
            raise commands.errors.BadArgument(
                f"Cannot find object: {objectid}. Make sure this bot can see it. If it was an emoji, make sure it was not a default one."
            )

    @commands.hybrid_command()
    @describe(
        term="The term to search urbanDictionary for.",
    )
    async def urban(self, ctx: commands.Context, term: str):
        """
        Searches the Urban Dictionary and returns the top results for a term
        """
        url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"

        params = {"term": term}

        headers = {
            "X-RapidAPI-Host": "mashape-community-urban-dictionary.p.rapidapi.com",
            "X-RapidAPI-Key": Config.X_RAPID_API_KEY,
        }

        response = requests.request("GET", url, headers=headers, params=params)
        res = response.json()["list"]
        embed = fmte(
            ctx,
            t="`{}`: {} Definitions {}".format(
                term, len(res), "[Showing 5]" if len(res) > 5 else ""
            ),
        )
        for d in res[:5]:
            embed.add_field(
                name="[{}]({})".format(d["author"], d["permalink"]),
                value="{}\n**Upvotes:** {}\n**Written On:** {}".format(
                    d["definition"], d["thumbs_up"], d["written_on"]
                ),
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @describe(
        term="The term to search urbanDictionary for.",
    )
    async def define(self, ctx: commands.Context, term: str):
        """
        Searches Merriam-Webster's Collegiate dictionary and returns the top results for a term
        """
        response = requests.get(
            "https://dictionaryapi.com/api/v3/references/collegiate/json/{}?key={}".format(
                term.lower(), Config.DICT_API_KEY
            )
        ).json()
        defs = []
        dates = []
        types = []
        for defi in response:
            if isinstance(defi, str):
                raise commands.errors.BadArgument(term)
            defs.append(
                (
                    "".join(
                        defi.get(
                            "shortdef",
                            [
                                "Unknown",
                            ],
                        )[0]
                    ).capitalize()
                )
            )
            dates.append(defi.get("date", "Unknown"))
            types.append(defi.get("fl", "Unknown"))

        embed = fmte(
            ctx,
        )
        if len(defs) < 1:
            raise ValueError("Word not found/no definition")

        for c, item in enumerate(defs[:5]):
            embed.add_field(
                name="Definition {}, {}: *`[{}]`*".format(
                    c + 1,
                    types[c].capitalize(),
                    str(dates[c])[: dates[c].index("{")]
                    if "{" in str(dates[c])
                    else str(dates[c]),
                ),
                value=item,
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @describe(
        zone="The timezone to get the time from.",
    )
    async def time(self, ctx: commands.Context, zone: str = "UTC"):
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
                d="```{}```".format(datetime.now(pytz.timezone(zone))),
            )
            await ctx.send(embed=embed)

    @time.autocomplete("zone")
    async def time_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=zone, value=zone)
            for zone in pytz.all_timezones
            if current.lower() in zone.lower()
        ][:25]

    @commands.hybrid_command()
    @discord.app_commands.rename(_time="time")
    async def timestamp(self, ctx: commands.Context, _time: TimeConvert):
        """
        Converts a string such as "1 hour 13 minutes" to a UNIX timestamp.
        """
        await ctx.send(_time + time.time())

    @commands.hybrid_command()
    async def eval(self, ctx: commands.Context):
        """
        Creates an asynchronous sandbox Python environment using SnekBox
        """
        await ctx.interaction.response.send_modal(CodeModal(ctx))


class CodeModal(BaseModal):
    def __init__(self, ctx: commands.Context) -> None:
        self.ctx = ctx
        self.bot = ctx.bot
        super().__init__(title=f"{ctx.author}: Python Evaluation")

    code = discord.ui.TextInput(
        label=f"Paste / Type Code Here",
        style=discord.TextStyle.long,
        placeholder="Please input text here...",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        start = time.time()
        url: str = "http://localhost:8060/eval"
        sess: aiohttp.ClientSession = self.bot.session
        code = f"""
from typing import *
async def main() -> Any:
{indent(self.code.value, '    ')}
import asyncio, typing
try:
    result: typing.Any = asyncio.run(main())
    if result is not None:
        print(result)
except ValueError:
    async def iterate() -> None:
        print([value async for value in main()])
    asyncio.run(iterate())
"""
        data = {"input": code}
        response = await sess.post(url, data=data)
        data = await response.json()

        color = discord.Color.teal() if data["returncode"] == 0 else discord.Color.red()
        buffer: io.BytesIO = io.BytesIO()
        buffer.write(bytes(data["stdout"][:EVALUATION_TRUNCATION_THRESHOLD], "UTF-8"))
        buffer.seek(0)
        file: discord.File = discord.File(buffer, filename="result.py")
        embed = fmte(
            self.ctx,
            t="Successful!" if data["returncode"] == 0 else "Error!",
            d=f"```py\n{self.code.value}\n```",
            c=color,
        )
        if data["returncode"] == 143:
            embed.title = "Signal Terminated"
        embed.add_field(
            name="Evaluation Time", value=f"{(time.time() - start) * 1000}ms"
        )
        await interaction.response.send_message(embed=embed, file=file)


async def setup(bot):
    await bot.add_cog(Utility(bot))
