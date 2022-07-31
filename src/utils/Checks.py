import re
from typing import Callable

from discord.ext import commands


def inter_choke(ctx: commands.Context):
    async def predicate():
        return True
    return commands.check(predicate)


def control_defer(defer: bool = True, thinking: bool = True, ephemeral: bool = False):
    def deco(func: Callable):
        func.defer = {"defer": defer, "thinking": thinking, "ephemeral": ephemeral}
        return func

    return deco


def is_valid_url(s: str):
    regex = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    return regex.match(s) is not None
