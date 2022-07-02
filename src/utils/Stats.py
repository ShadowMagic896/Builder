import discord
import os
from typing import Iterator, List


class Stats:
    def _get_lines(path: os.PathLike) -> Iterator:
        with open(path) as file:
            return len(file.readlines())

    def line_count(files: List[os.PathLike]):
        return sum([Stats._get_lines(file) for file in files])

    def invite_link(clientID: int, perms: int = 0):
        return discord.utils.oauth_url(clientID)
