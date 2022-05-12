import asyncio
from math import floor
from multiprocessing.sharedctypes import Value
from random import randint, random
from typing import Any, List, Optional, Union
import discord
from discord.ext import commands
from datetime import datetime


async def getv(inter) -> Union[commands.Context, None]:
    try:
        return await commands.Context.from_interaction(inter)
    except ValueError:
        return None


def fmte(
        ctx: commands.Context = None,
        t: str = "",
        d: str = "",
        c: discord.Color = discord.Color.teal(),
        u: discord.User = None,) -> discord.Embed:
    """
    Takes the sent information and returns an embed with a footer and timestamp added, with the default color being teal.
    """
    if not (ctx or u):
        raise Exception("my guy")
    user = ctx.author if not u else u
    if ctx:
        ti = ctx.bot.latency
    else:
        ti = (randint(50, 60) + randint(0, 99) / 100) / 1000  # This is ethical
    embed = discord.Embed(
        title=t,
        description=d,
        color=c
    )
    embed.set_author(
        name="Requested By: %s" %
        str(user), url="https://discordapp.com/users/%s" %
        user.id, icon_url=user.avatar.url)
    if ti:
        embed.set_footer(
            text="Response in %sms" % round(ti * 1000, 3)
        )
    embed.timestamp = datetime.now()
    return embed


def fmte_i(inter: discord.Interaction, t="", d="",
           c=discord.Color.teal()) -> discord.Embed:
    return fmte(t=t, d=d, c=c, u=inter.user)


def getReadableValues(seconds):
    hours = round(seconds // 3600)
    mins = round(seconds // 60 - hours * 60)
    secs = round(seconds // 1 - hours * 3600 - mins * 60)
    msec = str(round(seconds - hours * 3600 - mins * 60 - secs, 6))[2:]
    msec += "0" * (6 - len(msec))

    return(hours, mins, secs, msec)


class EmbedPaginator(discord.ui.View):
    """
    A neat little view that takes items and spreads them across multiple embed pages

    `values`: The values to use
    `pagesize`: How many items to display per page. Maximum of 36 [Discord limit]
    `fieldname`: Name of each field. This is used by calling `getattr` on each value in the `values`
    `fieldvalue`: Value of each field. This is used by calling `getattr` on each value in the `values`
    `defaultname`: What to name the fields if `fieldname` if not given or `getattr` returned None
    `defaultvalue`: What to name the fields if `fieldname` if not given or `getattr` returned None
    `embedinline`: Whether to have each field be invline in the embed or not.
    `startposition`: Page index to start at.
    `timeout`: Timeout for the interaction.

    In order for the `Close` button to work, the `response` attribute must be set to the message you want it to delete.

    FMTE [Format Embed] takes parts for an embed and constructs it, along with adding a timestamp, author, and color. (Very useful!)

    Examples:
    ```py
    # This takes all messages in the current channel's history and shows it using EmbedPaginator
    msgs = []
    async for m in ctx.channel.history(limit = 200):
        msgs.append(m)

    embed = fmte(
        ctx,
        t = "Waiting for user input...",
    )
    view = EmbedPaginator(
        values = msgs,
        pagesize = 10,
        fieldname = "content",
        fieldvalue = "author",
        defaultname = "`No Content`",
        defaultvalue = "`No author (?)`"
    )

    msg = await ctx.send(embed=embed, view=view)
    view.response = msg
    ```
    """

    def __init__(
        self, *,

        values: List[Any],
        pagesize: int,

        fieldname: str = None,
        fieldvalue: str = None,

        defaultname: str = None,
        defaultvalue: str = None,

        embedinline: bool = False,
        startpositon: int = 0,

        timeout: Optional[float] = 180
    ):
        self.pagesize: int = pagesize
        self.values: List[Any] = values

        self.curpos = startpositon
        self.maxpos: int = floor(len(self.values) / self.pagesize)

        self.titl = fieldname
        self.desc = fieldvalue

        self.dftl = defaultname
        self.dfdc = defaultvalue

        self.inln = embedinline

        self.response: discord.Message = ...

        super().__init__(timeout=timeout)

    @discord.ui.button(label="<<")
    async def fullback(self, inter: discord.Interaction, _: Any):
        self.curpos = 0

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="<")
    async def back(self, inter: discord.Interaction, _: Any):
        self.curpos -= 1

        if self.curpos < 0:
            self.curpos = self.maxpos  # Loop to end

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌")
    async def close(self, inter: discord.Interaction, _: Any):
        await self.response.delete()

    @discord.ui.button(label=">")
    async def next(self, inter: discord.Interaction, _: Any):
        self.curpos += 1

        if self.curpos > self.maxpos:
            self.curpos = 0  # Loop back to beginning

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label=">>")
    async def fullnext(self, inter: discord.Interaction, _: Any):
        self.curpos = self.maxpos

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter,
            t="[{}/{}]".format(self.curpos + 1, self.maxpos + 1)
        )

    def add_fields(self, embed: discord.Embed) -> discord.Embed:
        for value in self.values[self.pagesize *
                                 (self.curpos):self.pagesize * (self.curpos + 1)]:

            embed.add_field(
                name=getattr(
                    value,
                    self.titl) if self.titl and getattr(
                    value,
                    self.titl) else str(
                    self.dftl),
                value=getattr(
                    value,
                    self.desc) if self.desc and getattr(
                    value,
                    self.desc) else str(
                    self.dfdc),
                inline=self.inln
            )
        return embed


class DMEmbedPaginator(discord.ui.View):
    """
    A neat little view that takes items and spreads them across multiple embed pages

    `values`: The values to use
    `pagesize`: How many items to display per page. Maximum of 36 [Discord limit]
    `fieldname`: Name of each field. This is used by calling `getattr` on each value in the `values`
    `fieldvalue`: Value of each field. This is used by calling `getattr` on each value in the `values`
    `defaultname`: What to name the fields if `fieldname` if not given or `getattr` returned None
    `defaultvalue`: What to name the fields if `fieldname` if not given or `getattr` returned None
    `embedinline`: Whether to have each field be invline in the embed or not.
    `startposition`: Page index to start at.
    `timeout`: Timeout for the interaction.

    In order for the `Close` button to work, the `response` attribute must be set to the message you want it to delete.

    FMTE [Format Embed] takes parts for an embed and constructs it, along with adding a timestamp, author, and color. (Very useful!)

    Examples:
    ```py
    # This takes all messages in the current channel's history and shows it using EmbedPaginator
    msgs = []
    async for m in ctx.channel.history(limit = 200):
        msgs.append(m)

    embed = fmte(
        ctx,
        t = "Waiting for user input...",
    )
    view = EmbedPaginator(
        values = msgs,
        pagesize = 10,
        fieldname = "content",
        fieldvalue = "author",
        defaultname = "`No Content`",
        defaultvalue = "`No author (?)`"
    )

    msg = await ctx.send(embed=embed, view=view)
    view.response = msg
    ```
    """

    def __init__(
        self, *,

        values: List[Any],
        pagesize: int,

        fieldname: str = None,
        fieldvalue: str = None,

        defaultname: str = None,
        defaultvalue: str = None,

        embedinline: bool = False,
        startpositon: int = 0,

        timeout: Optional[float] = 180
    ):
        self.pagesize: int = pagesize
        self.values: List[Any] = values

        self.curpos = startpositon
        self.maxpos: int = floor(len(self.values) / self.pagesize)

        self.titl = fieldname
        self.desc = fieldvalue

        self.dftl = defaultname
        self.dfdc = defaultvalue

        self.inln = embedinline

        self.response: discord.Message = ...

        super().__init__(timeout=timeout)

    @discord.ui.button(label="<<")
    async def fullback(self, inter: discord.Interaction, _: Any):
        self.curpos = 0

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="<")
    async def back(self, inter: discord.Interaction, _: Any):
        self.curpos -= 1

        if self.curpos < 0:
            self.curpos = self.maxpos  # Loop to end

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌")
    async def close(self, inter: discord.Interaction, _: Any):
        await self.response.delete()

    @discord.ui.button(label=">")
    async def next(self, inter: discord.Interaction, _: Any):
        self.curpos += 1

        if self.curpos > self.maxpos:
            self.curpos = 0  # Loop back to beginning

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label=">>")
    async def fullnext(self, inter: discord.Interaction, _: Any):
        self.curpos = self.maxpos

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter,
            t="[{}/{}]".format(self.curpos + 1, self.maxpos + 1)
        )

    def add_fields(self, embed: discord.Embed) -> discord.Embed:
        for value in self.values[self.pagesize *
                                 (self.curpos):self.pagesize * (self.curpos + 1)]:

            embed.add_field(
                name=getattr(
                    value,
                    self.titl) if self.titl and getattr(
                    value,
                    self.titl) else str(
                    self.dftl),
                value=[
                    r.url for r in getattr(
                        value,
                        self.desc)] if self.desc and getattr(
                    value,
                    self.desc) else str(
                    self.dfdc),
                inline=self.inln
            )
        return embed


class Desc:
    user = "The target of this command."
    ephemeral = "Whether to publicly show the response to the command."
    reason = "The reason for using this command. Shows up in the server's audit log."
