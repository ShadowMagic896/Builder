from enum import Enum
from typing import Mapping, NamedTuple

from PIL import ImageFont

from .constants import Timers


class DDGSearchData(NamedTuple):
    title: str
    url: str
    body: str
    feature_type: "FeatureType"


class DDGImageData(NamedTuple):
    title: str
    thumbnail: str
    url: str


class FeatureType(Enum):
    result: int = 0
    video: int = 1
    image: int = 2


class NHSearchData(NamedTuple):
    title: str
    code: int
    thumbnail: str


class PHSearchData(NamedTuple):
    title: str
    thumbnail: str
    link: str
    duration: str


class Cache(NamedTuple):
    RTFM: Mapping["RTFMCache", "RTFMMeta"]  # type: ignore
    fonts: "Fonts"


class Fonts(NamedTuple):
    bookosbi: ImageFont.FreeTypeFont


class RTFMCache(NamedTuple):
    project: str
    query: str
    version: str
    lang: str
    timestamp: float

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, RTFMCache):
            return NotImplemented
        else:
            return all(
                (
                    self.project == __o.project,
                    self.query == __o.query,
                    self.version == __o.version,
                    self.lang == __o.lang,
                    self.timestamp == __o.timestamp,
                )
            )

    def round_to_track(timestamp: float) -> int:
        """
        Returns the timestamp of the object to the nearest multiple of 120
        """
        return round(timestamp / Timers.RTFM_CACHE_CLEAR) * Timers.RTFM_CACHE_CLEAR

    def __hash__(self) -> int:
        return hash((self.project, self.query, self.version, self.lang, self.timestamp))
