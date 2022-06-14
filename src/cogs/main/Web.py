import asyncio
import functools
from io import BytesIO
from typing import Any, Callable, ItemsView, List, Optional
from typing_extensions import Self
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord import app_commands
from discord.app_commands import describe, Range
from discord.ext import commands

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib import parse

from src.utils.converters import UrlGet, UrlFind
from src.utils.embeds import fmte
from bot import Builder, BuilderContext
from src.utils.subclass import Paginator
from src.utils.types import GoogleSearchData
from src.utils.parsers import Parser
from src.utils.coro import run


class Web(commands.Cog):
    """
    The wonders of the interwebs!
    """

    def __init__(self, bot: Builder, driver: webdriver.Chrome) -> None:
        self.bot = bot
        self.driver: webdriver.Chrome = driver

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
        data = parse.urlsplit(url[0])

        embed = fmte(ctx, t="URL Information")
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
            path = parse.urlsplit(url).path
            rev: str = str(path)[::-1]

            if "." not in rev or rev.index(
                    "/") < rev.index("."):  # No format attached
                ext: str = "txt"
            else:
                ext = path[(len(rev) - rev.index(".")):]
        else:
            ext = fmt
        embed = fmte(ctx, t="Request Sent, Response Recieved", d=url)
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
        await ctx.interaction.response.defer()
        self.driver.get(url[0])
        await asyncio.sleep(wait)
        buffer: BytesIO = BytesIO(await run(self.driver.get_screenshot_as_png))
        file = discord.File(buffer, filename="image.png")
        embed = fmte(ctx, t="Screenshot Captured")
        embed.set_image(url="attachment://image.png")
        await ctx.send(embed=embed, file=file)

    @web.command()
    @commands.is_nsfw()
    @describe(
        query="What to search for",
    )
    async def search(self, ctx: BuilderContext, query: str):
        """
        Searches the web for links
        """
        url: str = f"https://www.google.com/search?q={parse.quote_plus(query)}"
        data: List[GoogleSearchData] = [
            data
            async for data in Parser(self.bot.session, url).googleSearch(self.driver)
        ]
        view = GoogleView(ctx, query, data)
        embed = await view.page_zero(ctx.interaction)
        await view.check_buttons()
        await ctx.send(embed=embed, view=view)


class GoogleView(Paginator):
    def __init__(
        self,
        ctx: BuilderContext,
        q: str,
        values: List[GoogleSearchData],
        *,
        timeout: Optional[float] = 45,
    ):
        self.q = q
        super().__init__(ctx, values, 5, timeout=timeout)

    async def adjust(self, embed: discord.Embed):
        start = self.pagesize * (self.position - 1)
        stop = self.pagesize * self.position
        values: List[GoogleSearchData] = self.vals[start:stop]
        for co, data in enumerate(values):
            fmt_co = str(co + 1 + (self.position - 1)
                         * self.pagesize).rjust(2, "0")
            embed.description += f"\n**`{fmt_co}`: [{data.title}]({data.url})**\n*{data.body or 'Google gave no body...'}*"
        return embed

    async def embed(self, inter: discord.Interaction):
        return fmte(
            self.ctx,
            t=f"Results: {self.q}\nPage `{self.position}` of `{self.maxpos or 1}` [{len(self.vals)} Results]",
        )


async def setup(bot: commands.Bot):
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.headless = True
    driver: webdriver.Chrome = await run(webdriver.Chrome, options=options)
    driver.set_window_size(1920, 1080)
    await bot.add_cog(Web(bot, driver))
