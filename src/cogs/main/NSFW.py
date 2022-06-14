import asyncio
from typing import List, Literal, Optional
import aiohttp
import bs4
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

import os
import random
from bs4 import BeautifulSoup
from src.utils.types import NHSearchData
from data.environ import NSFW_PATH

from src.utils.subclass import Paginator
from src.utils.parsers import Parser
from src.utils.embeds import fmte, fmte_i
from bot import BuilderContext
from src.utils.constants import Const


class NSFW(commands.Cog):
    """
    For the horny ones
    """

    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot

    def ge(self):
        return "\N{NO ONE UNDER EIGHTEEN SYMBOL}"

    @commands.hybrid_command()
    # @commands.is_nsfw()
    @describe(
        query="The keywords to search for.",
    )
    async def rule34(self, ctx: BuilderContext, query: str):
        """
        Gets images from [rule34.xxx](https://rule34.xxx]) and sends the first 10 images to you.
        """
        query = query.replace(" ", "+")
        res = await (
            await self.bot.session.get(
                Const.URLs.RULE_34 + f"index.php?page=post&s=list&tags=%s)" % query
            )
        ).text()
        soup = BeautifulSoup(res, "html.parser")

        tags = soup.select(
            "div[id=content] > div[id=post-list] > div[class=content] > div[class=image-list] > *"
        )

        urls = []

        embed = fmte(ctx, t="Results found...", d="Sending to author.")
        await ctx.send(embed=embed)

        for tag in tags:
            soup = BeautifulSoup(str(tag), "html.parser")
            url = soup.select_one("span[class=thumb] > a > img")["src"]
            urls.append(url)

        for url in urls[:10]:
            embed = fmte(
                ctx,
                t="R34 Request For: `{}`".format(" ".join(query)),
                d="[Source]({})".format(url),
            )
            embed.set_image(url=url)
            await ctx.author.send(embed=embed)

    @commands.hybrid_command()
    # @commands.is_nsfw()
    @describe(
        amount="The amount of images to send.",
    )
    async def neko(
        self,
        ctx: BuilderContext,
        amount: Range[int, 1, 20] = 1,
    ):
        """
        Gets an image response from [nekos.life](https://nekos.life) and sends it to you.
        """

        data = []

        for co in range(amount):
            res = await (await self.bot.session.get(Const.URLs.NEKO_LIFE)).text()
            soup = BeautifulSoup(res, "html.parser")
            img = soup.find_all("img")
            data.append(img[0]["src"])

        embed = fmte(
            ctx,
            t="Fetched Images",
            d="Sending...",
        )
        await ctx.send(embed=embed)

        for l in data:
            embed = fmte(
                ctx,
            )
            embed.set_image(url=l)
            await ctx.author.send(embed=embed)

    @commands.hybrid_command()
    # @commands.is_nsfw()
    @describe(
        amount="The amount of images to send.",
    )
    async def nekolewd(
        self,
        ctx: BuilderContext,
        amount: Range[int, 1, 20] = 1,
    ):
        """
        Gets an image response from [nekos.life/lewd](https://nekos.life/lewd) and sends it to you.
        """
        mdir = NSFW_PATH + "Nekos/"
        data = []

        for co in range(amount):
            data.append(
                discord.File(
                    mdir +
                    random.choice(
                        os.listdir(mdir)),
                    "Neko.jpg"))

        embed = fmte(
            ctx,
            t="Fetched Images",
            d="Sending...",
        )

        await ctx.send(embed=embed)

        for l in data:
            embed = fmte(
                ctx,
            )
            await ctx.author.send(embed=embed, file=l)
            await asyncio.sleep(1)

    @commands.hybrid_group()
    async def nhentai(self, ctx: BuilderContext):
        pass

    @nhentai.command()
    @describe(
        code="The code to search for.",
    )
    async def get(self, ctx: BuilderContext, code: int):
        """
        Uses [nhentai.xxx](https://nhentai.xxx) to get all pages within a manga, and sends them to you.
        """
        meta: NHGetMeta = await NHGetMeta.create(ctx, code)
        view = NHentaiGetView(meta=meta)
        embed = await view.page_zero(ctx.interaction)
        await view.check_buttons()
        await ctx.send(embed=embed, view=view)

    @nhentai.command()
    @describe(
        query="The keyword to search for.",
    )
    async def search(
        self,
        ctx: BuilderContext,
        query: str,
        sort: Optional[Literal["recent", "today", "week", "all-time"]] = "all-time",
    ):
        """
        Searches for manga on [nhentai.xxx](https://nhentai.xxx) and returns the top results.
        """
        meta = await NHSearchMeta.create(ctx, query, sort)
        view = NHSearchView(meta)
        await view.check_buttons()
        embed = await view.page_zero(ctx.interaction)
        view.message = await ctx.send(embed=embed, view=view)


class NHSearchMeta:
    @classmethod
    async def create(cls, ctx: BuilderContext, query: str, sort: str):
        base_sort: str = "&sort=popular"
        fmt_dict = {
            "today": base_sort + "-today",
            "week": base_sort + "-week",
            "week": base_sort + "-week",
            "all-time": "",
        }
        sort = fmt_dict.get(query, "")
        url = Const.URLs.NHENTAI + f"search/?q={query}{sort}"
        data = [x async for x in Parser(ctx.bot.session, url).nh_search()]

        cls.ctx = ctx
        cls.query = query
        cls.data = data

        return cls


class NHSearchView(Paginator):
    def __init__(
        self,
        meta: NHSearchMeta,
        *,
        timeout: Optional[float] = 45,
    ):
        self.meta = meta
        super().__init__(self.meta.ctx, range(len(self.meta.data)), 1, timeout=timeout)

    async def adjust(self, embed: discord.Embed):
        value: NHSearchData = self.meta.data[self.position - 1]
        url = f"[Visit URL]({Const.URls.NHENTAI}g/{value.code})"
        embed.add_field(name="Name:", value=value.name, inline=False)
        embed.add_field(name="URL:", value=url, inline=False)
        embed.add_field(name="HNentai Code:", value=value.code, inline=False)
        embed.set_image(url=value.thumbnail)

        return embed

    async def embed(self, inter: discord.Interaction):
        return fmte(
            self.ctx,
            f"NHentai Search Results for `{self.meta.query}`: `{self.position}` / `{self.maxpos or 1}`",
        )

    @discord.ui.button(label="Select This", emoji="\N{BLACK RIGHTWARDS ARROW}")
    async def viewthis(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer()
        meta = await NHGetMeta.create(self.ctx, self.meta.data[self.position - 1].code)
        view = NHentaiGetView(meta)
        embed = await view.page_zero(inter)
        await view.check_buttons()
        view.message = await self.meta.ctx.interaction.followup.send(
            embed=embed, view=view, wait=True
        )


class NHGetMeta:
    @classmethod
    async def create(cls, ctx: BuilderContext, code: int):
        """
        Get the base metadata for a page
        """
        result: aiohttp.ClientResponse = await ctx.bot.session.get(
            f"{Const.URls.NHENTAI}g/{code}/1"
        )
        if result.status != 200:
            raise ValueError(
                "I could not find that code. Please double-check your spelling,"
            )

        text = await result.text()
        soup = bs4.BeautifulSoup(text, "html.parser")

        dataurl = soup.select(
            "body > div#page-container > section#image-container > a > img"
        )[0]["src"]
        datacode = dataurl[26:-6]

        __pages = soup.select(
            "body > div#page-container > section#pagination-page-bottom > a.last"
        )[0]["href"]

        substring = f"/g/{code}/"
        codestart = str(__pages)[:-1].index(substring) + len(substring)
        pages = int(__pages[codestart:-1])

        baseurl = Const.URLs.NHENTAI_CDN + f"g/{datacode}/"

        cls.ctx: BuilderContext = ctx

        cls.code: int = code
        cls.datacode: int = datacode

        cls.pages: int = pages

        cls.baseurl = baseurl
        return cls


class NHentaiGetView(Paginator):
    def __init__(
        self,
        meta: NHGetMeta,
        *,
        timeout: Optional[float] = 180,
    ):
        self.meta = meta
        super().__init__(
            self.meta.ctx, list(range(self.meta.pages)), 1, timeout=timeout
        )

    async def adjust(self, embed: discord.Embed):
        image_url: str = f"{self.meta.baseurl}{self.position}.jpg"
        embed.set_image(url=image_url)
        return embed

    async def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter,
            t=f"NHentai `{self.meta.code}`: `{self.position}` / `{self.maxpos or 1}`",
        )


async def setup(bot):
    await bot.add_cog(NSFW(bot))
