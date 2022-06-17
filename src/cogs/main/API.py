import asyncio
from copy import copy
import functools
import time
from typing import List, Mapping, Optional
from webbrowser import Chrome
import aiohttp
from selenium import webdriver
from urllib.parse import quote_plus
from bs4 import BeautifulSoup, ResultSet, Tag
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

from bot import Builder, BuilderContext
from src.utils.api import evaulate_response
from src.utils.embeds import fmte
from src.utils.subclass import Paginator
from src.utils.errors import NoDocumentsFound
from src.utils.constants import Const
from src.utils.coro import run
from src.utils.types import RTFMCache


class API(commands.Cog):
    """
    Using external APIs! Suggestion one with /suggest
    """

    def __init__(self, bot: Builder) -> None:
        self.bot = bot
        super().__init__()

    def ge(self):
        return "\N{Clockwise Rightwards and Leftwards Open Circle Arrows}"  # Bruh

    @commands.hybrid_command()
    @describe(
        project="The project to search",
        query="What to search for",
        version="The project version to search on",
        lang="What language to search on",
    )
    async def rtfm(
        self,
        ctx: commands.Context,
        project: str,
        query: str,
        version: str = "stable",
        lang="en",
    ):
        """
        Read the F*cking Manual: Seach readthedocs.io
        """

        meta = await RTFMMeta.create(ctx, self.bot.driver, project, query, version, lang)
        view = RTFMPaginator(meta, 10)
        embed = await view.page_zero(ctx.interaction)
        await view.check_buttons()
        view.message = await ctx.send(embed=embed, view=view)

    @rtfm.autocomplete("project")
    async def project_autocomplte(self, inter: discord.Interaction, current: str):
        query = quote_plus(current)
        params: dict = {}
        if (lang := getattr(inter.namespace, "lang", None)) is not None:
            params["language"] = lang
        params["q"] = query
        url: str = f"{Const.URLs.RTD}/search"
        response: aiohttp.ClientResponse = await self.bot.session.get(
            url, params=params
        )
        response.raise_for_status()
        text: str = await response.text()

        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")
        selector: str = "div#content > div.wrapper > div.navigable > div > div.module > div.module-wrapper > div.module-list > div.module-list-wrapper > ul > li.module-item.search-result-item"
        results: ResultSet[Tag] = soup.select(selector, limit=25)

        choices: List[discord.app_commands.Choice] = []
        for result in results:
            name = result.select_one("p.module-item-title > a").text.strip()
            name = name[: name.index("(")].strip()

            choices.append(
                discord.app_commands.Choice(
                    name=name or "--- UNNAMED ---", value=name or "--- UNNAMED ---"
                )
            )
        return choices

    @rtfm.autocomplete("version")
    async def version_autocomplete(self, inter: discord.Interaction, current: str):
        if (proj := (getattr(inter.namespace, "project", None))) is None:
            return discord.app_commands.Choice(
                name="--- Please enter a project first ---", value="latest"
            )
        proj = proj.replace(".", "")
        url: str = f"https://readthedocs.org/projects/{proj}/"
        response: aiohttp.ClientResponse = await self.bot.session.get(url)
        text: str = await response.text()

        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")
        selector: str = "div#project_details > div.wrapper > div.module > div.module-list > div.module-list-wrapper > ul > li"

        versions: ResultSet[Tag] = soup.select(selector, limit=25)
        results: List[discord.app_commands.Choice] = []

        for version in versions:
            name = version.select_one("a").text.strip()
            if name.lower() in current.lower() or current.lower() in name.lower():
                results.append(discord.app_commands.Choice(name=name, value=name))

        return results

    @rtfm.autocomplete("lang")
    async def lang_autocomplete(self, inter: discord.Interaction, current: str):
        if (proj := (getattr(inter.namespace, "project", None))) is None:
            return discord.app_commands.Choice(
                name="--- Please enter a project first ---", value="en"
            )
        proj = proj.replace(".", "")
        url: str = Const.URLs.RTD + f"projects/{proj}/"
        response: aiohttp.ClientResponse = await self.bot.session.get(url)
        text: str = await response.text()

        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")
        selector: str = "div#project_details > div.wrapper > div.project_details > ul"

        translatons: ResultSet[Tag] = soup.select_one(selector).select("li", limit=25)
        results: List[discord.app_commands.Choice] = []

        for translaton in translatons:
            name = translaton.select_one("a").text.strip()
            results.append(discord.app_commands.Choice(name=name, value=name))
        # This erroneously assumes that all projects have a translation for english
        # But I have to because the static webpage only gives languages other than english, and
        # Loading the JS webpage with selenium is slow and expensive, so I guess it works like
        # 99% of the time, which is ok with me
        if "en" not in [r.name for r in results]:
            results.append(discord.app_commands.Choice(name="en", value="en"))

        return results

    @commands.hybrid_group()
    async def openai(self, ctx: BuilderContext):
        pass

    @openai.command()
    @describe(
        message="The message to detect",
    )
    async def filter(self, ctx: BuilderContext, message: str):
        """
        Detects the estimated unsafe content coming from a message. Errs on the side of caution
        """
        preset = APIPresets.OpenAI.detect(message, 1)
        response: dict = await run(
            self.bot.loop, self.bot.openai.Completion.create, **preset
        )
        code: int = int(evaulate_response(response))
        if code == 0:
            embed = fmte(
                ctx,
                t="This Text is Safe",
                c=discord.Color.teal(),
            )
        elif code == 1:
            embed = fmte(
                ctx,
                t="This text is sensitive.",
                d="This means that the text could be talking about a sensitive topic, something political, religious, or talking about a protected class such as race or nationality.",
                c=discord.Color.yellow(),
            )
        else:
            embed = fmte(
                ctx,
                t="This text is unsafe.",
                d="This means that the text contains profane language, prejudiced or hateful language, something that could be NSFW, or text that portrays certain groups/people in a harmful manner.",
                c=discord.Color.red(),
            )
        await ctx.send(embed=embed)

    @openai.command()
    @describe(
        message="The message to complete or respond to",
        stochasticism="How random the response is",
    )
    async def complete(
        self, ctx: BuilderContext, message: str, stochasticism: Range[float, 0, 1] = 0.5
    ):
        """
        Autocompltetes a sentence or responds to a question
        """
        preset = APIPresets.OpenAI.complete(message, stochasticism)
        response: dict = await run(
            self.bot.loop, self.bot.openai.Completion.create, **preset
        )
        embed = fmte(ctx, t="Completion Finished")
        for choice in response["choices"]:
            embed.add_field(name=f"Choice {choice['index']+1}:", value=choice["text"])
        await ctx.send(embed=embed)

    @openai.command()
    @describe(
        message="The text to fix",
        stochasticism="How random the response is",
    )
    async def grammar(
        self,
        ctx: BuilderContext,
        message: str,
        edits: Range[int, 1, 5] = 1,
        stochasticism: Range[float, 0, 1] = 0.5,
    ):
        """
        Fixes grammar in a statement
        """
        preset = APIPresets.OpenAI.grammar(message, edits, stochasticism)
        response: dict = await run(self.bot.loop, self.bot.openai.Edit.create, **preset)
        embed = fmte(ctx, t="Checking Completed")
        for choice in response["choices"]:
            embed.add_field(name=f"Choice {choice['index']+1}:", value=choice["text"])
        await ctx.send(embed=embed)

    @openai.command()
    @describe(
        message="The message to edit",
        instructions="How to edit the message. The more specific, the better",
        edits="How many times to edit the message",
        stochasticism="How random the response is",
    )
    async def edit(
        self,
        ctx: BuilderContext,
        message: str,
        instructions: str,
        edits: Range[int, 1, 5] = 1,
        stochasticism: Range[float, 0, 1] = 0.5,
    ):
        """
        Attempts to edit a message based upon instructions
        """
        preset = APIPresets.OpenAI.gen_edit(message, instructions, edits, stochasticism)
        response: dict = await run(self.bot.loop, self.bot.openai.Edit.create, **preset)
        embed = fmte(ctx, t="Editing Completed")
        for choice in response["choices"]:
            embed.add_field(name=f"Choice {choice['index']+1}:", value=choice["text"])
        await ctx.send(embed=embed)

    async def run(loop: asyncio.BaseEventLoop, func, *args, **kwargs):
        part = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, part)


class APIPresets:
    class OpenAI:
        def detect(text: str):
            return {
                "model": "content-filter-alpha",
                "prompt": f"<|endoftext|>{text}\n--\nLabel:",
                "temperature": 0,
                "max_tokens": 1,
                "top_p": 0,
                "logprobs": 10,
            }

        def complete(text: str, temp: float):
            return {
                "model": "text-davinci-001",
                "temperature": temp,
                "prompt": text,
                "max_tokens": 2000,
            }

        def grammar(text: str, edits: int, stochasticism: float):
            return {
                "model": "text-davinci-edit-001",
                "input": text,
                "instruction": "Fix all spelling mistakes",
                "temperature": stochasticism,
                "n": edits,
            }

        def gen_edit(text: str, inst: str, edits: int, stochasticism: float):

            return {
                "model": "text-davinci-edit-001",
                "input": text,
                "instruction": inst,
                "temperature": stochasticism,
                "n": edits,
            }


class RTFMMeta:
    @classmethod
    async def create(
        cls,
        ctx: BuilderContext,
        driver: webdriver.Chrome,
        project: str,
        query: str,
        version: str,
        lang: str,
    ):
        async def retrieve(project: str, query: str, version: str, lang: str):
            project: str = project.replace(".", "")
            c_query = copy(query)
            query: str = quote_plus(query)
            reference_url: str = f"https://{project}.readthedocs.io/{lang}/{version}/"
            url: str = (
                f"https://{project}.readthedocs.io/{lang}/{version}/search.html?q={query}"
            )

            await run(driver.get, url)
            text = await run(
                driver.execute_script,
                "return document.documentElement.outerHTML",
            )
            soup: BeautifulSoup = BeautifulSoup(text, "html.parser")

            select: str = (
                "div.main-grid > main.grid-item > div#search-results > ul.search > li"
            )
            results: ResultSet[Tag] = soup.select(select)

            if len(results) == 0:
                raise NoDocumentsFound("No documents for those parameters were found.")

            cls.ctx = ctx
            cls.ref = reference_url
            cls.project = project
            cls.query = query
            cls.query_raw = c_query
            cls.version = version
            cls.lang = lang
            cls.values = results

            return cls
        searcher = RTFMCache(
            project.lower().replace(".", ""),
            query.lower(),
            version.lower(),
            lang.lower(),
            RTFMCache.round_to_track(time.time())
        )
    
        if (cache := ctx.bot.caches.RTFM.get(
            searcher, None
        )) is None:
            results = await retrieve(project, query, version, lang)
            searcher = RTFMCache(
                results.project.lower().replace(".",""),
                results.query.lower(),
                results.version.lower(),
                results.lang.lower(),
                RTFMCache.round_to_track(time.time())
            )
            ctx.bot.caches.RTFM[searcher] = results
            return results, 1
        return cache, 0


class RTFMPaginator(Paginator):
    def __init__(self, meta: RTFMMeta, pagesize: int, *, timeout: Optional[float] = 45):
        self.was_cached: bool = meta[1] == 0
        self.meta = meta[0]
        super().__init__(self.meta.ctx, self.meta.values, pagesize, timeout=timeout)

    async def embed(self, inter: discord.Interaction):
        return fmte(
            self.ctx,
            t=f"`{self.meta.project}`/`{self.meta.version}`: `{self.meta.query_raw}`\nPage `{self.position+1}` of `{self.maxpos+1}` [`{len(self.meta.values)}` Results]",
        )

    async def adjust(self, embed: discord.Embed):
        for co, value in enumerate(self.value_range):
            name = value.select_one("a").text
            link = value.select_one("a")["href"]

            embed.description += (
                f"**`{self.fmt_abs_pos(co)}`:** [`{name}`]({self.meta.ref + link})\n"
            )
        
        if self.was_cached:
            embed.description += f"This result was cached. It will in decache in {Const.Timers.RTFM_CACHE_CLEAR - round(time.time() % Const.Timers.RTFM_CACHE_CLEAR)} seconds"
        return embed


async def setup(bot: Builder):
    await bot.add_cog(API(bot))
