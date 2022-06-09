from collections import namedtuple
from typing import NamedTuple


class GoogleSearchData(NamedTuple):
    """
    Represesnts a result packet with website title, URL, and body
    """

    title: str
    url: str
    body: str


class NHSearchData(NamedTuple):
    """
    Represents a result packet with a code, thumbnail, and name
    """

    code: int
    thumbnail: str
    name: str
