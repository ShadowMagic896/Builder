import asyncio
from typing import Optional, Tuple
import aiohttp
import bs4
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

import os
import random
from bs4 import BeautifulSoup
from data.Config import NSFW_PATH
from src.auxiliary.user.Subclass import Paginator

from src.auxiliary.user.Embeds import fmte, fmte_i


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
        querey="The keywords to search for.",
    )
    async def rule34(self, ctx: commands.Context, querey: str):
        """
        Gets images from [rule34.xxx](https://rule34.xxx]) and sends the first 10 images to you.
        """
        querey = querey.replace(" ", "+")
        res = await (
            await self.bot.session.get(
                f"https://rule34.xxx/index.php?page=post&s=list&tags=%s)" % querey
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
                t="R34 Request For: `{}`".format(" ".join(querey)),
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
        ctx: commands.Context,
        amount: Range[int, 1, 20] = 1,
    ):
        """
        Gets an image response from [nekos.life](https://nekos.life) and sends it to you.
        """

        data = []

        for co in range(amount):
            res = await (await self.bot.session.get(f"https://nekos.life")).text()
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
        ctx: commands.Context,
        amount: Range[int, 1, 20] = 1,
    ):
        """
        Gets an image response from [nekos.life/lewd](https://nekos.life/lewd) and sends it to you.
        """
        mdir = NSFW_PATH + "Nekos/"
        data = []

        for co in range(amount):
            data.append(
                discord.File(mdir + random.choice(os.listdir(mdir)), "Neko.jpg")
            )

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

    @commands.hybrid_command()
    # @commands.is_nsfw()
    @describe(
        code="The code to search for.",
    )
    async def nhentai(self, ctx: commands.Context, code: int):
        """
        Uses [nhentai.xxx](https://nhentai.xxx) to get all pages within a manga, and sends them to you.
        """
        meta: NHMeta = await NHMeta.create(ctx, code)
        view = NHentaiView(meta=meta)
        embed = await view.page_zero(ctx.interaction)
        await view.checkButtons()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    # @commands.is_nsfw()
    @describe(
        querey="The keywords to search for.",
    )
    async def nhsearch(self, ctx: commands.Context, querey: str):
        """
        Searches for manga on [nhentai.xxx](https://nhentai.xxx) and returns the top results.
        """
        querey = querey.replace(" ", "+")
        url = "https://nhentai.xxx/search/?q=%s" % querey
        res = await (await self.bot.session.get(url)).text()
        parse = BeautifulSoup(res, "html.parser")
        codes = []
        images = []
        names = []

        embed = fmte(ctx, t="Fetched Images", d="Sending...")
        await ctx.send(embed=embed)

        for i in parse.find_all("div")[3:-1]:
            try:
                if not parse.select_one("div > a"):
                    continue
                nparse = BeautifulSoup(str(i), "html.parser")
                codes.append(nparse.select_one("div > a")["href"][3:-1])
                images.append(nparse.select_one("div > a > img")["src"])
                names.append(nparse.select_one("div > a > div"))
            except BaseException:
                continue

        if not len(codes) == len(images) == len(names):
            embed = fmte(
                ctx,
                t="Something odd happened, results may be incorrect. If so, please try another search.",
            )
        else:
            embed = fmte(
                ctx, t="{} results found, sending to author...".format(len(codes))
            )
        await ctx.send(embed=embed)
        for n in range(min(codes.__len__(), images.__len__(), names.__len__())):
            c = n + 1
            tot = min(codes.__len__(), images.__len__(), names.__len__())

            name = str(names[n])[21:-6][:235]
            code = str(codes[n])
            url = str(images[n])
            embed = fmte(ctx, t="{} / {}\n{} [{}]".format(c, tot, name, code))
            embed.set_image(url=url)
            await ctx.author.send(embed=embed)


class NHMeta:
    @classmethod
    async def create(cls, ctx: commands.Context, code: int):
        """
        Get the base metadata for a page
        """
        result: aiohttp.ClientResponse = await ctx.bot.session.get(
            f"https://nhentai.xxx/g/{code}/1"
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

        baseurl = f"https://cdn.nhentai.xxx/g/{datacode}/"

        cls.ctx: commands.Context = ctx

        cls.code: int = code
        cls.datacode: int = datacode

        cls.pages: int = pages

        cls.baseurl = baseurl
        return cls


class NHentaiView(Paginator):
    def __init__(
        self,
        meta: NHMeta,
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
            inter, t=f"`{self.meta.code}`: `{self.position}` / `{self.maxpos or 1}`"
        )


async def setup(bot):
    await bot.add_cog(NSFW(bot))
