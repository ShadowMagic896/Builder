from enum import Enum
from typing import NamedTuple


class DDGSearchData(NamedTuple):
    title: str
    url: str
    body: str
    feature_type: "FeatureType"


class FeatureType(Enum):
    link: int = 0
    video_module: int = 1
    image_module: int = 2


class NHSearchData(NamedTuple):
    code: int
    thumbnail: str
    name: str


class PHSearchData(NamedTuple):
    name: str
    thumbnail: str
    link: str
    duration: str
