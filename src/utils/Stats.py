import os
from typing import Iterator, List
import discord


class Stats:
    def __iter_lines(directory: os.PathLike) -> Iterator:
        for file in os.listdir(directory):

            path = f"{directory}/{file}"
            if file[0] in [".", "_"]:
                continue

            if os.path.isdir(path):
                yield from Stats.__iter_lines(path)
            else:
                if not path.endswith(".py"):
                    continue
                with open(path) as f:
                    yield len(f.readlines())

    def line_count(directories: List[os.PathLike]):
        return sum([sum(Stats.__iter_lines(directory)) for directory in directories])

    def invite_link(clientID: int, perms: int = 0):
        return discord.utils.oauth_url(clientID)
