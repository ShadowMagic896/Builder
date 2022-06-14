import asyncio
from enum import Enum
import time
from timeit import timeit
from typing import AsyncIterator
from typing_extensions import Self
import aiohttp
from bs4 import BeautifulSoup, ResultSet, Tag
from src.utils.types import FeatureType, GoogleSearchData, NHSearchData
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

    async def ddg_search(self, driver) -> AsyncIterator[GoogleSearchData]:
        # Running Selenium here forces DDG to treat me as a user
        await run(driver.get, self.url)
        text = await run(
            driver.execute_script, "return document.documentElement.outerHTML"
        )
        parse: BeautifulSoup = BeautifulSoup(text, "html.parser")
        selector: str = "div.results--main > div#links > div"
        items: ResultSet[Tag] = await run(parse.select, selector)
        for item in items:
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
                    feature_type: FeatureType = FeatureType.video_module

                    yield GoogleSearchData(title, url, body, feature_type)
                if "module--images" in item.select_one("div")["class"]:  # Image Results
                    query: str = self.url[self.url.index("=") + 1 :]
                    url: str = f"https://duckduckgo.com/?q={query}&iax=images&ia=images"
                    title: str = item.select("div > span")[1].text
                    images: ResultSet[Tag] = item.select(
                        "div > div.module--images__thumbnails.js-images-thumbnails > div"
                    )
                    body: str = f"{len(images)} Images"
                    feature_type: FeatureType = FeatureType.image_module

                    yield GoogleSearchData(title, url, body, feature_type)

            else:
                if "nrn-react-div" not in item["class"]:
                    continue
                components: ResultSet[Tag] = item.select("article > div")
                url: str = components[0].select_one("div > a")["href"]
                title: str = components[1].select_one("h2 > a > span").text
                body: str = components[2].select_one("div > span").text
                feature_type: FeatureType = FeatureType.link

                yield GoogleSearchData(title, url, body, feature_type)

            feature_type: FeatureType
