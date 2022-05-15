import asyncio
from dataclasses import MISSING
from datetime import datetime
from concurrent import futures
import pytz
from src.auxiliary.user.Converters import TimeConvert
from src.auxiliary.user.Subclass import AutoModal
from src.auxiliary.user.Embeds import fmte
import time
import discord
from discord.app_commands import describe
from discord.ext import commands

import os
from typing import Any, List
from data.config import Config

import aiofiles

import bs4
import requests
import warnings
warnings.filterwarnings("error")


class Utility(commands.Cog):
    """
    Helpful stuff
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.container_users: List[int] = []
        pass

    def ge(self):
        return "\N{INPUT SYMBOL FOR NUMBERS}"

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
            permissions=discord.Permissions(0),
            scopes=["bot", "applications.commands"],
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
        emt = "`\N{OCTAGONAL SIGN} [HIGH]`" if ping > 0.4 else "`\N{WARNING SIGN} [MEDIUM]`"
        emt = emt if ping > 0.2 else "`\N{WHITE HEAVY CHECK MARK} [LOW]`"

        await ctx.send(embed=fmte(ctx, "\N{TABLE TENNIS PADDLE AND BALL} Pong!", f"{round(ping*1000, 3)} miliseconds!\n{emt}"), ephemeral=ephemeral)

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
    async def find(self, ctx: commands.Context, objectid: str, ephemeral: bool = False):
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
            "X-RapidAPI-Key": Config().X_RAPID_API_KEY}

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
                term.lower(), Config().DICT_API_KEY)).json()
        defs = []
        dates = []
        types = []
        for defi in response:
            if isinstance(defi, str):
                raise commands.errors.BadArgument(term)
            defs.append(("".join(defi.get("shortdef", ["Unknown",])[0]).capitalize()))
            dates.append(defi.get("date", "Unknown"))
            types.append(defi.get("fl", "Unknown"))

        embed = fmte(ctx,)
        if len(defs) < 1:
            raise ValueError('Word not found/no definition')


        for c, item in enumerate(defs[:5]):
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
        await ctx.send(embed=embed, ephemeral=ephemeral)
    
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

    @commands.hybrid_command()
    async def timestamp(self, ctx: commands.Context, time: TimeConvert):
        """
        Converts a string such as "1 hour 13 minutes" to a UNIX timestamp.
        """
        await ctx.send(str(time) + time.time())

    @commands.hybrid_command()
    @commands.cooldown(2, 60*60*4, commands.BucketType.user)
    async def container(self, ctx: commands.Context):
        """
        Creates a docker container and runs Python code inside of it.
        """
        if ctx.author.id in self.container_users:
            raise commands.err
        await ctx.interaction.response.send_modal(CodeModal(ctx))

class CodeModal(discord.ui.Modal):
    def __init__(self, ctx) -> None:
        self.ctx: commands.Context = ctx
        super().__init__(title="Python Evaluation")
    code = discord.ui.TextInput(
        label="Please paste / type code here",
        style=discord.TextStyle.long
    )

    def makeContainer(self) -> os.PathLike:
        """
        Runs a contianer. Returns the result log path.
        """

        value: str = self.code.value

        basepath = f"{os.getcwd()}\docker"

        # Prepare Files for Building
        _dir = len(os.listdir(f"{basepath}\containers"))
        dirpath = f"{basepath}\containers\{_dir}"
        os.system(f"mkdir {dirpath}")

        pypath = f"{dirpath}\main.py"

        targ_dockerfile = f"{dirpath}\Dockerfile"
        tmpl_dockerfile = f"{basepath}\Dockerfile"

        with open(pypath, "w") as pyfile:
            pyfile.write(value)

        with open(targ_dockerfile, "w") as target:
            with open(tmpl_dockerfile, "r") as template:
                target.write(template.read())

        pylog = f"{dirpath}\\pythonlog.txt"
        os.system(f"cd {dirpath} && docker build -t {_dir} . && docker run -t {_dir} > {pylog}")
        
        # Cleanup
        os.system(f"docker container prune --force && docker image prune -a --force")
        return pylog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        estart = time.time()

        loop = asyncio.get_event_loop()
        with futures.ThreadPoolExecutor() as pool:
            logpath: os.PathLike = await loop.run_in_executor(pool, self.makeContainer)

        embed = fmte(
            self.ctx,
            d = f"**Code:**\n```py\n{self.code.value}\n\n# Finished in: {time.time() - estart} seconds```"
        )

        file = discord.File(logpath, "pythonlog.txt")
        await interaction.followup.send(content=None, embed=embed, file=file)
        file.close()
        os.system(f"rd /Q /S {logpath}\\..\\")


async def setup(bot):
    await bot.add_cog(Utility(bot))
