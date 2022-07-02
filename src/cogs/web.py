import asyncio
import discord
import logging
from bs4 import BeautifulSoup, ResultSet, Tag
from copy import copy
from discord import app_commands
from discord.app_commands import Range, describe
from discord.ext import commands
from io import BytesIO
from typing import List, Optional
from urllib import parse as libparse

from ..utils import parse as utparse
from ..utils.bot_types import Builder, BuilderContext
from ..utils.converters import UrlFind, UrlGet
from ..utils.coro import run
from ..utils.embeds import format
from ..utils.subclass import BaseCog, Paginator
from ..utils.types import DDGImageData, DDGSearchData, FeatureType


class Web(BaseCog):
    """
    The wonders of the interwebs!
    """

    def ge(self):
        return "\N{GLOBE WITH MERIDIANS}"

    @commands.hybrid_group()
    async def web(self, ctx: BuilderContext):
        pass

    @web.command()
    @describe(url="The URL to analyze")
    async def parse(self, ctx: BuilderContext, url: UrlFind):
        """
        Gathers data about a URL. Does not actually get any data from the server.
        """
        data = libparse.urlsplit(url[0])

        embed = await format(ctx, title="URL Information")
        embed.add_field(name="Scheme", value=f"`{data.scheme or None}`")
        embed.add_field(name="NetLoc", value=f"`{data.netloc or None}`")
        embed.add_field(name="Path", value=f"`{data.path or None}`")
        embed.add_field(name="Query", value=f"`{data.query or None}`")
        embed.add_field(name="Fragment", value=f"`{data.fragment or None}`")
        embed.add_field(name="Host Name", value=f"`{data.hostname or None}`")
        embed.add_field(name="Port #", value=f"`{data.port or None}`")
        embed.add_field(name="Username", value=f"`{data.username or None}`")
        embed.add_field(name="Password", value=f"`{data.password or None}`")

        await ctx.send(embed=embed)

    @web.command()
    @app_commands.rename(response="url")
    @describe(
        response="The URL to get",
        fmt="How to format the response. Leave empty to automatically detect",
    )
    async def get(
        self, ctx: BuilderContext, response: UrlGet, fmt: Optional[str] = "Auto"
    ):
        """
        Gets the direct response payload of a request
        """
        url = str(response.url)
        if fmt == "Auto":
            path = libparse.urlsplit(url).path
            rev: str = str(path)[::-1]

            if "." not in rev or rev.index("/") < rev.index("."):  # No format attached
                ext: str = "txt"
            else:
                ext = path[(len(rev) - rev.index(".")) :]
        else:
            ext = fmt
        embed = await format(ctx, title="Request Sent, Response Recieved", desc=url)
        embed.add_field(name="Format Used:", value=ext)
        buffer: BytesIO = BytesIO(await response.read())
        file = discord.File(buffer, filename=f"response.{ext}")
        await ctx.send(embed=embed, file=file)

    @web.command()
    @describe(
        url="The URL to get a screenshot of",
        wait="How long to wait for the page to load",
    )
    async def screenshot(
        self, ctx: BuilderContext, url: UrlFind, wait: Range[int, 0, 25] = 0
    ):
        """
        Get a screenshot of a webpage
        """
        self.bot.driver.get(url[0])
        await asyncio.sleep(wait)
        buffer: BytesIO = BytesIO(await run(self.bot.driver.get_screenshot_as_png))
        file = discord.File(buffer, filename="image.png")
        embed = await format(ctx, title="Screenshot Captured")
        embed.set_image(url="attachment://image.png")
        await ctx.send(embed=embed, file=file)

    @web.command()
    @describe(
        query="What to search for",
    )
    async def search(self, ctx: BuilderContext, query: str):
        """
        Searches duckduckgo.com for a query
        """
        meta = await DDGSearchMeta.create(ctx, query)
        view = DDGSearchView(meta)
        embed = await view.page_zero(ctx.interaction)
        await view.check_buttons()
        view.message = await ctx.send(embed=embed, view=view)

    @web.command()
    @describe(query="What to search for")
    async def image(self, ctx: BuilderContext, query: str):
        """
        Searches duckduckgo.com for an image
        """
        meta = await DDGImageMeta.create(ctx, query)
        view = DDGImageView(meta)
        embed = await view.page_zero(ctx.interaction)
        await view.check_buttons()
        view.message = await ctx.send(embed=embed, view=view)


class DDGSearchMeta:
    @classmethod
    async def create(cls, ctx: BuilderContext, query: str):
        url: str = f"https://duckduckgo.com/?q={utparse.quote(query)}&kp=-2"
        original = copy(url)
        await run(ctx.bot.driver.get, url)
        text = await run(
            ctx.bot.driver.execute_script, "return document.documentElement.outerHTML"
        )
        parse: BeautifulSoup = BeautifulSoup(text, "html.parser")
        selector: str = "div.results--main > div#links > div"
        items: ResultSet[Tag] = await run(parse.select, selector)
        cls.data: List[DDGSearchData] = []
        for item in items:
            try:
                if "module-slot" in item["class"]:  # Special result
                    if not item.select_one("div"):
                        continue
                    if (
                        "module--carousel-videos" in item.select_one("div")["class"]
                    ):  # Video
                        data: Tag = item.select_one(
                            "div > div.module--carousel__wrap > div > div > div > div.module--carousel__body > a"
                        )
                        url: str = data["href"]
                        title: str = data["title"]
                        body: str = data.text
                        feature_type: FeatureType = FeatureType.video

                        cls.data.append(DDGSearchData(title, url, body, feature_type))
                    if (
                        "module--images" in item.select_one("div")["class"]
                    ):  # Image Results
                        query: str = url[url.index("=") + 1 :]
                        url: str = (
                            f"https://duckduckgo.com/?q={query}&iax=images&ia=images"
                        )
                        title: str = item.select("div > span")[1].text
                        images: ResultSet[Tag] = item.select(
                            "div > div.module--images__thumbnails.js-images-thumbnails > div"
                        )
                        body: str = f"{len(images)} Images"
                        feature_type: FeatureType = FeatureType.image

                        cls.data.append(DDGSearchData(title, url, body, feature_type))

                else:
                    if "nrn-react-div" not in item["class"]:
                        continue
                    components: ResultSet[Tag] = item.select("article > div")
                    url: str = components[0].select_one("div > a")["href"]
                    title: str = components[1].select_one("h2 > a > span").text
                    body: str = components[2].select_one("div > span").text
                    feature_type: FeatureType = FeatureType.result

                    cls.data.append(DDGSearchData(title, url, body, feature_type))
            except Exception as e:
                continue

        cls.ctx = ctx
        cls.query = query
        cls.url = original
        return cls


class DDGSearchView(Paginator):
    def __init__(
        self,
        meta: DDGSearchMeta,
        *,
        timeout: Optional[float] = 45,
    ):
        self.meta = meta
        super().__init__(meta.ctx, meta.data, 5, timeout=timeout)

    async def adjust(self, embed: discord.Embed):
        for co, data in enumerate(self.value_range):
            if data.feature_type == FeatureType.result:
                embed.description += f"\n**`{self.format_absoloute(co)}`: [{data.title}]({data.url})**\n*{data.body}*"
            elif data.feature_type == FeatureType.video:
                embed.description += f"\n**`{self.format_absoloute(co)}`: VIDEO: [{data.title}]({data.url})**\n*{data.body}*"
            elif data.feature_type == FeatureType.image:
                embed.description += f"\n**`{self.format_absoloute(co)}`: IMAGES: [{data.title}]({data.url})**\n*{data.body}*"
            else:
                logging.error(f"Unknown data type in DDG Seach: {data.feature_type}")
        return embed

    async def embed(self, inter: discord.Interaction):
        return await format(
            self.meta.ctx,
            title=f"Results: {self.meta.query}\nPage `{self.position+1}` of `{self.maxpos+1}` [{len(self.values)} Results]",
        )


class DDGImageMeta:
    @classmethod
    async def create(cls, ctx: BuilderContext, query: str):
        url: str = f"https://duckduckgo.com/?t=ffab&q={utparse.quote(query)}&iar=images&iax=images&ia=images&kp=-2"
        await run(ctx.bot.driver.get, url)
        await asyncio.sleep(1)
        text = await run(
            ctx.bot.driver.execute_script, "return document.documentElement.outerHTML"
        )
        parse: BeautifulSoup = BeautifulSoup(text, "html.parser")

        cls.data: List[DDGImageData] = []

        selector: str = "div > div.tile-wrap > div > div.tile"
        for item in parse.select(selector, limit=25):
            try:
                title: str = item.select_one("a > span.tile--img__title").text
                thumbnail: str = (
                    "https:"
                    + item.select_one(
                        "div.tile--img__media > span.tile--img__media__i > img"
                    )["data-src"]
                )
                url: str = item.select_one("a > span.tile--img__domain")["title"]
                data: DDGSearchData = DDGImageData(title, thumbnail, url)
                cls.data.append(data)
            except BaseException:  # Incomplete image, stop looking
                break

        cls.ctx = ctx
        cls.query = query
        return cls


class DDGImageView(Paginator):
    def __init__(self, meta: DDGImageMeta, *, timeout: Optional[float] = 45):
        self.meta = meta
        super().__init__(meta.ctx, meta.data, 1, timeout=timeout)

    async def adjust(self, embed: discord.Embed):
        value: DDGImageData = self.values[self.position]

        embed.description = f"[{value.title}]({value.url})"
        embed.set_image(url=value.thumbnail)
        return embed

    async def embed(self, inter: discord.Interaction):
        return await format(
            self.meta.ctx,
            title=f"Image Results: `{self.meta.query}`\nPage `{self.position+1}` of `{self.maxpos+1}` [{len(self.values)} Results]",
        )


async def setup(bot: Builder):
    await bot.add_cog(Web(bot))
