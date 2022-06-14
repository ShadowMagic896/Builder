from collections import namedtuple
from enum import Enum
from typing import NamedTuple


class GoogleSearchData(NamedTuple):
    """
    Represesnts a result packet with website title, URL, and body
    """

    title: str
    url: str
    body: str
    feature_type: "FeatureType"


class FeatureType(Enum):
    link: int = 0
    video_module: int = 1
    image_module: int = 2


class NHSearchData(NamedTuple):
    """
    Represents a result packet with a code, thumbnail, and name
    """

    code: int
    thumbnail: str
    name: str
