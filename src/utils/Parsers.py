from typing import AsyncIterator
from typing_extensions import Self
import aiohttp
from bs4 import BeautifulSoup, ResultSet, Tag
from src.utils.Types import GoogleSearchData, NHSearchData


class Parser:
    def __init__(self, session: aiohttp.ClientSession, url: str) -> None:
        self.session = session
        self.url = url

    async def nhentaiSearch(self) -> AsyncIterator[NHSearchData]:
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

    async def googleSearch(self: Self) -> AsyncIterator[GoogleSearchData]:
        response: aiohttp.ClientResponse = await self.session.get(self.url)
        response.raise_for_status()
        parse: BeautifulSoup = BeautifulSoup(await response.text(), "html.parser")
        selector: str = "body > div#main > div#center_col > div#res > div#search > div > div#rso > div"
        for item in parse.select(selector):
            xsoup: BeautifulSoup = BeautifulSoup(str(item), "html.parser")

            # The last item is a spacer between it and the next item
            xitems = xsoup.select("div > div")[:-1]
            meta_packet = xitems[0].select_one("div > a")

            url: str = meta_packet["href"]
            title: str = meta_packet.select_one("h3").text
            body: str = xitems[1].select_one("div > div > span").text

            yield GoogleSearchData(title, url, body)
