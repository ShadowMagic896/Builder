from typing import AsyncIterator, Generator, List, Tuple
import aiohttp
from bs4 import BeautifulSoup, Tag
import pyppeteer
from src.ext.Types import GoogleSearchData, NHSearchData


class Parser:
    def __init__(self, session: aiohttp.ClientSession, url: str) -> None:
        self.session = session
        self.url = url

    async def nhentaiSearch(self) -> AsyncIterator[NHSearchData]:
        res = await self.session.get(self.url)
        res.raise_for_status()
        parse = BeautifulSoup(await res.text(), "html.parser")

        gallery = parse.select("body > div.container.index-container > div")
        for image in gallery:
            nparse = BeautifulSoup(str(image), "html.parser")
            code: int = nparse.select_one("div > a")["href"][3:-1]
            thumbnail: str = nparse.select_one("div > a > img")["src"]
            name: str = nparse.select_one("div > a > div").text

            yield NHSearchData(code, thumbnail, name)

    async def googleSearch(self) -> AsyncIterator[GoogleSearchData]:
        response: aiohttp.ClientResponse = await self.session.get(self.url)
        response.raise_for_status()
        parse = BeautifulSoup(await response.text(), "html.parser")
        selector = "body > div#main > div#center_col > div#res > div#search > div > div#rso > div"
        for item in parse.select(selector):
            xsoup = BeautifulSoup(str(item), "html.parser")
            xitems = xsoup.select("div > div")[
                :-1
            ]  # The last item is a spacer between it and the next item
            meta_packet = xitems[0].select_one("div > a")
            url: str = meta_packet["href"]
            title: str = meta_packet.select_one("h3").text
            body: str = xitems[1].select_one("div > div > span").text

            yield GoogleSearchData(title, url, body)
