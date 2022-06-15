from enum import Enum
from typing import NamedTuple


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
