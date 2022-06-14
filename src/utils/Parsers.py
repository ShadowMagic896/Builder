import asyncio
from typing import AsyncIterator
from typing_extensions import Self
import aiohttp
from bs4 import BeautifulSoup, ResultSet, Tag
from src.utils.types import GoogleSearchData, NHSearchData
from src.utils.coro import run


class Parser:
    def __init__(self, session: aiohttp.ClientSession, url: str) -> None:
        self.session = session
        self.url = url

    async def nh_search(self) -> AsyncIterator[NHSearchData]:
        res: aiohttp.ClientResponse = await self.session.get(self.url)
        res.raise_for_status()
        parse: BeautifulSoup = BeautifulSoup(await res.text(), "html.parser")

        selector: str = "body > div.container.index-container > div"

        for image in parse.select(selector):
            nparse: BeautifulSoup = BeautifulSoup(str(image), "html.parser")
            code: int = nparse.select_one("div > a")["href"][3:-1]
            thumbnail: str = nparse.select_one("div > a > img")["src"]
            name: str = nparse.select_one("div > a > div").text

            yield NHSearchData(code, thumbnail, name)

    async def googleSearch(self, driver) -> AsyncIterator[GoogleSearchData]:
        # Running Selenium here forces Google to treat me as a user
        await run(driver.get, self.url)
        text = await run(
            driver.execute_script, "return document.documentElement.outerHTML"
        )
        parse: BeautifulSoup = BeautifulSoup(text, "html.parser")
        selector: str = "div#center_col > div#res > div#search > div > div#rso > div"
        items = await run(parse.select, selector)
        for item in items:

            # Unwrap primary results
            if "hlcw0c" in item.get("class", []):
                item = item.select_one("div")
            # Get rid of results that aren't just URL and text (videos, "People Also Ask", etc.)
            if "tF2Cxc" not in item.get("class", []):
                continue
            xsoup: BeautifulSoup = BeautifulSoup(str(item), "html.parser")

            # The last item is a spacer between it and the next item
            xitems = xsoup.select("div > div")[:-1]
            meta_packet = xitems[0].select_one("div > a")

            url: str = meta_packet["href"]
            title: str = meta_packet.select_one("h3").text
            desc_feature = [
                v for v in xitems if v.get("data-content-feature", None) == "1"
            ][0]
            body: str = desc_feature.select_one("div > div").text

            yield GoogleSearchData(title, url, body)
