import aiohttp
from datetime import datetime
import io
from textwrap import indent
import pytz
from settings import EVALUATION_TRUNCATION_THRESHOLD
import time

import discord
from discord.app_commands import describe
from discord.ext import commands

from typing import Any, List, Optional, Tuple
import environ
import requests
import warnings
from src.utils.embeds import fmte
from src.utils.subclass import BaseCog, BaseModal, BaseView
from src.utils.converters import TimeConvert
from src.utils.errors import *
from bot import Builder, BuilderContext

warnings.filterwarnings("error")


class Utility(BaseCog):
    """
    Helpful stuff
    """

    def __init__(self, bot: Builder) -> None:
        self.bot: Builder = bot
        self.jobs: List[int] = []

    def ge(self):
        return "\N{INPUT SYMBOL FOR NUMBERS}"

    @commands.hybrid_command()
    @describe()
    async def ping(self, ctx: BuilderContext):
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
    async def info(self, ctx: BuilderContext, user: discord.Member = None):
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
    async def bot(self, ctx: BuilderContext):
        """
        Returns information about the bot.
        """
        b = "\nㅤㅤ"
        bb = "\nㅤㅤㅤ"
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
    @describe(
        objectid="The ID of the object to look for.",
    )
    async def find(self, ctx: BuilderContext, objectid: str):
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
    async def urban(self, ctx: BuilderContext, term: str):
        """
        Searches the Urban Dictionary and returns the top results for a term
        """
        url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"

        params = {"term": term}

        headers = {
            "X-RapidAPI-Host": "mashape-community-urban-dictionary.p.rapidapi.com",
            "X-RapidAPI-Key": environ.X_RAPID_API_KEY,
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
        term="The term to define",
    )
    async def define(self, ctx: BuilderContext, term: str):
        """
        Searches Merriam-Webster's Collegiate dictionary and returns the top results for a term
        """
        response = requests.get(
            "https://dictionaryapi.com/api/v3/references/collegiate/json/{}?key={}".format(
                term.lower(), environ.DICT_API_KEY
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
    async def time(self, ctx: BuilderContext, zone: str = "UTC"):
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
    async def timestamp(self, ctx: BuilderContext, _time: TimeConvert):
        """
        Converts a string such as "1 hour 13 minutes" to a UNIX timestamp.
        """
        await ctx.send(_time + time.time())

    @commands.hybrid_command()
    async def eval(self, ctx: BuilderContext):
        """
        Creates an asynchronous sandbox Python environment using SnekBox
        """
        await ctx.interaction.response.send_modal(CodeModal(ctx))

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def embed(self, ctx: BuilderContext):
        """
        Customize and send an embed. Not just for bots!
        """
        embed: discord.Embed = fmte(ctx, t="Untitled")
        embed.remove_footer()
        view = EmbedView(ctx, embed)
        view.message = await ctx.send(embed=embed, view=view, ephemeral=True)


class CodeModal(BaseModal):
    def __init__(self, ctx: BuilderContext) -> None:
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
async def main():
{indent(self.code.value, '    ').replace('"', "'")}
import asyncio, typing, warnings
if asyncio.iscoroutinefunction(main):
    result = asyncio.run(main())
    print(result)
else:
    async def iter():
        [print(v) async for v in main()]
    asyncio.run(iter())
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


class EmbedView(BaseView):
    def __init__(
        self, ctx: BuilderContext, embed: discord.Embed, timeout: Optional[float] = 300
    ):
        self.tinter: Optional[discord.Interaction] = None
        self.embed = embed
        super().__init__(ctx, timeout)

    @discord.ui.button(label="Set Title")
    async def title(self, inter: discord.Interaction, button: discord.ui.Button):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Set Title")

            _title: discord.ui.TextInput = discord.ui.TextInput(
                label="Please Input Title"
            )

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                self.embed.title = str(_self._title.value)
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(label="Set Description")
    async def description(self, inter: discord.Interaction, button: discord.ui.Button):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Set Description")

            description: discord.ui.TextInput = discord.ui.TextInput(
                label="Please Input Description"
            )

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                self.embed.description = str(_self.description.value)
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(label="Set Color")
    async def setcolor(self, inter: discord.Interaction, button: discord.ui.Button):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Set Color")

            col = discord.ui.TextInput(label="Please Input the Hex Color Value")

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                v = _self.col.value
                if not v.startswith("0x"):
                    v = f"0x{v}"
                try:
                    c = int(v, 16)
                except ValueError:
                    raise commands.errors.BadArgument("Not a valid hexadecimal value")
                self.embed.color = discord.Color(c)
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(label="Add Field")
    async def addfield(self, inter: discord.Interaction, button: discord.ui.Button):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Add Field")

            name: discord.ui.TextInput = discord.ui.TextInput(
                label="Please Input Field Name"
            )
            value: discord.ui.TextInput = discord.ui.TextInput(
                label="Please Input Field Value"
            )
            inline = discord.ui.Select(
                placeholder="Will This Be In-Line?",
                options=[
                    discord.SelectOption(label="Yes", value=True),
                    discord.SelectOption(label="No", value=False),
                ],
            )

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                self.embed.add_field(
                    name=str(_self.name),
                    value=str(_self.value),
                    inline=_self.inline.values[0] == "True",
                )
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(label="Remove Field")
    async def removefield(self, inter: discord.Interaction, button: discord.ui.Button):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Remove Field")

            field: discord.ui.TextInput = discord.ui.TextInput(
                label="Which Field # do you Want to Remove?"
            )

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                try:
                    f = int(_self.field.value)
                except ValueError:
                    raise commands.errors.BadArgument("Not a valid number")
                if f > len(self.embed.fields) or f < 1:
                    raise commands.errors.BadArgument("That field does not exist")
                self.embed.clear_fields()
                for c, e in enumerate(self.embed.fields):
                    if c == f - 1:
                        continue
                    self.embed.add_field(name=e.name, value=e.value, inline=e.inline)
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(label="Set Image URL")
    async def setimage(self, inter: discord.Interaction, button: discord.ui.Button):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Set Image")

            url: discord.ui.TextInput = discord.ui.TextInput(
                label="Please Input Image URL"
            )

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                self.embed.set_image(url=str(_self.url.value))
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(label="Set Thumbnail URL")
    async def setthumbnail(self, inter: discord.Interaction, button: discord.ui.Button):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Set Thumbnail")

            url: discord.ui.TextInput = discord.ui.TextInput(
                label="Please Input Image URL"
            )

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                self.embed.set_thumbnail(url=str(_self.url.value))
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(label="Set Footer Text")
    async def setfootertext(
        self, inter: discord.Interaction, button: discord.ui.Button
    ):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Set Footer Text")

            url: discord.ui.TextInput = discord.ui.TextInput(
                label="Please Input Footer Text"
            )

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                if self.embed.footer.icon_url:
                    self.embed.set_footer(
                        text=_self.url.value, icon_url=str(self.embed.footer.icon_url)
                    )
                else:
                    self.embed.set_footer(text=_self.url.value)
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(label="Set Footer Image URL")
    async def setfooterurl(self, inter: discord.Interaction, button: discord.ui.Button):
        class UpdateModal(BaseModal):
            def __init__(_self) -> None:
                super().__init__(title="Set Footer Image URL")

            url: discord.ui.TextInput = discord.ui.TextInput(
                label="Please Input Footer Image URL"
            )

            async def on_submit(_self, interaction: discord.Interaction) -> None:
                if self.embed.footer:
                    self.embed.set_footer(
                        text=self.embed.footer.text, icon_url=str(_self.url.value)
                    )
                else:
                    self.embed.set_footer(icon_url=str(_self.url.value))
                await interaction.response.edit_message(embed=self.embed)

        await inter.response.send_modal(UpdateModal())

    @discord.ui.button(
        label="Send",
        emoji="\N{BLACK RIGHTWARDS ARROW}",
        row=2,
        style=discord.ButtonStyle.green,
    )
    async def send(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.send_message(embed=self.embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
