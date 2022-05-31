import asyncio
from asyncio.subprocess import Process
from datetime import datetime
import io
from timeit import timeit
import pytz
from bot import Builder
from src.auxiliary.user.Converters import TimeConvert
from src.auxiliary.user.Subclass import BaseModal
from src.auxiliary.user.Embeds import fmte
import time
import discord
from discord.app_commands import describe
from discord.ext import commands

import os
from typing import Any, List, Tuple
from data import config
from data.errors import *
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

        botlat = self.bot.latency
        results.append(
            ("\N{Shinto Shrine} Gateway Latency", (botlat, getSym(botlat, 0.045)))
        )

        st = time.time()
        await self.bot.apg.execute("SELECT 1")
        end = time.time() - st
        results.append(("\N{Floppy Disk} Database Latency", (end, getSym(end, 0.001))))

        st = time.time()
        await self.bot.session.get("https://www.google.com")
        end = time.time() - st
        results.append(
            (
                "\N{Globe with Meridians} AioHTTP Latency [Google]",
                (end, getSym(end, 0.175)),
            )
        )

        # print(results)
        embed = fmte(ctx, t="\N{Table Tennis Paddle and Ball} Pong!")
        for res in results:
            embed.add_field(
                name=f"**{res[0]}**",
                value=f"```ansi\n\u001b[0;34m{round(res[1][0] * 1000, 5)}ms\n{res[1][1]}```",
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
        querey="What to search for.",
    )
    async def search(self, ctx: commands.Context, querey: str):
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
            "X-RapidAPI-Key": config.X_RAPID_API_KEY,
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
                term.lower(), config.DICT_API_KEY
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
    async def timestamp(self, ctx: commands.Context, time: TimeConvert):
        """
        Converts a string such as "1 hour 13 minutes" to a UNIX timestamp.
        """
        await ctx.send(str(time) + time.time())

    @commands.hybrid_command()
    # @commands.cooldown(2, 60 * 60 * 4, commands.BucketType.user)
    async def container(self, ctx: commands.Context):
        """
        Creates a docker container and runs Python code inside of it.
        """
        if ctx.author.id in self.container_users:
            raise commands.errors.MissingPermissions(
                "You are already running a container."
            )
        await ctx.interaction.response.send_modal(CodeModal(self, ctx))


class CodeModal(BaseModal):
    def __init__(self, util: Utility, ctx: commands.Context) -> None:
        self.util = util
        self.ctx: commands.Context = ctx
        super().__init__(title="Python Evaluation")

    code = discord.ui.TextInput(
        label="Please paste / type code here", style=discord.TextStyle.long
    )

    async def makeContainer(self, ctx: commands.Context, inter: discord.Interaction):
        """
        Runs a contianer. Returns the result STDOUT, STDERR, and return code.
        """
        if ctx.author.id not in [
            mem.id for mem in (await ctx.bot.application_info()).team.members
        ]:
            self.util.container_users.append(ctx.author.id)
        value: str = self.code.value
        basepath = f"{os.getcwd()}\docker"

        # Prepare Files for Building
        _dir = len(os.listdir(f"{basepath}\containers"))
        dirpath = f"{basepath}\containers\{_dir}"
        os.system(f"mkdir {dirpath}")

        pypath = f"{dirpath}\main.py"
        with open(pypath, "w") as pyfile:
            pyfile.write(value)

        for f in os.listdir(f"{basepath}\\template"):
            with open(f"{basepath}\\template\\{f}", "r") as template:
                with open(f"{dirpath}\\{f}", "w") as file:
                    file.write(template.read())

        options = {
            "--rm": "",
            "--memory": "6MB",
            "--ulimit": "cpu=3",
            "--read-only": "",
            "-t": _dir,
        }
        opts = " ".join(
            f"{x}{' ' if y != '' else y}{y}" for x, y in list(options.items())
        )

        # Build the Container
        await (
            await asyncio.create_subprocess_shell(
                f"cd {dirpath} && docker build -t {_dir} . ",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        ).communicate()
        print("Communicated")
        embed = fmte(
            ctx,
            t=f"Container Created `[ID: {_dir}]`",
            d="Compiling and running code...",
        )
        await inter.followup.send(embed=embed)
        proc: Process = await asyncio.create_subprocess_shell(
            f"cd {dirpath} && docker run {opts}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stderr:
            raise InternalError("This server's Docker daemon is not running right now.")

        # Cleanup
        await (
            await asyncio.create_subprocess_shell(
                f"docker image prune -a --force",
            )
        ).communicate()
        try:
            self.util.container_users.remove(self.ctx.author.id)
        except ValueError:
            pass

        return (_dir, stdout, (proc.returncode or 0))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        estart = time.time()
        await interaction.response.defer(thinking=True)
        _dir, stdout, return_code = await self.makeContainer(self.ctx, interaction)

        file: discord.File = ...
        color: discord.Color = ...

        color = discord.Color.teal() if return_code == 0 else discord.Color.red()

        buffer = io.BytesIO()
        buffer.write(stdout)
        buffer.seek(0)

        file = discord.File(buffer)
        file.filename = f"result.{self.ctx.author.id}.py"
        file.description = f"This is the result of a Python script written by Discord user {self.ctx.author.id}, and run in a Docker container."

        embed = fmte(
            self.ctx,
            d=f"```py\n{self.code.value}\n\n# Finished in: {time.time() - estart} seconds\n# Written by: {self.ctx.author.id}```",
            c=color,
        )

        await (await interaction.original_message()).edit(
            content=None, embed=embed, attachments=(file,)
        )
        ddir = os.getcwd() + f"\\docker\\containers\\{_dir}"
        os.system(f"rd /Q /S {ddir}")


async def setup(bot):
    await bot.add_cog(Utility(bot))
