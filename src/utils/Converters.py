import asyncio
from typing import Any, List, Literal, Optional, Set, Type, Union
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context
import numpy as np
from src.utils.functions import find_url
from src.utils.constants import Cogs
from src.utils.item_maps import Chemistry, get_atomic_name
import re

from src.utils.errors import ForbiddenData, MissingCog, MissingCommand, ScopeError


class TimeConvert(commands.Converter):
    async def convert(self, ctx: Context, inp: str):
        inp = inp.replace(" ", "").lower()
        breaker = "([0-9]+.{1})+"

        replacements = {
            "y": ["year", "years", "yr", "yrs", "ys"],
            "w": ["week", "weeks", "ws"],
            "d": ["day", "days", "ds"],
            "h": ["hour", "hours", "hr", "hrs", "hs"],
            "m": ["minute", "minutes", "min", "mins", "ms"],
            "s": ["seconds", "second", "sec", "secs"],
        }

        times = {  # Seconds for each one
            "w": 604800,
            "d": 86400,
            "h": 3600,
            "m": 60,
            "s": 1,
        }

        for key, value in list(replacements.items()):
            for r in value:
                inp = inp.replace(r, key)

        if not (matched := re.search(breaker, inp).group()):
            raise commands.errors.BadArgument("Invalid Time: %s" % matched)

        totaltime, counter = 0, ""
        for char in matched:
            if char.isdigit():
                counter += char
            else:
                totaltime += times[char] * int(counter)
                counter = ""
        return totaltime


class ListConverter(commands.Converter):
    def __init__(self, convtype: Type) -> None:
        self.convtype = convtype
        super().__init__()

    async def convert(self, ctx: Context, argument: str):
        argument = argument.replace(" ", "")
        match = (
            "\\[?(\\-?[\\d\\.]+,?\\s*)+\\]?"
            if self.convtype in [float, int]
            else "\\[?(\\-?[^,]+,?\\s*)+\\]?"
        )
        if not (res := re.search(match, argument).group()):
            raise commands.errors.BadArgument(argument)
        return self.strToList(res, self.convtype)

    def strToList(self, string: str) -> List[Any]:
        return [
            self.convtype(a)
            for a in string.replace("[", "")
            .replace("]", "")
            .replace(" ", "")
            .split(",")
        ]


class XY(commands.Converter):
    def __init__(self, dtype: type) -> None:
        self.dtype = dtype
        super().__init__()

    async def convert(self, ctx: Context, argument: str) -> np.ndarray:
        arr = np.array(argument.strip(r"[],{}").split(","), dtype=self.dtype)
        if len(arr) != 2:
            raise ValueError
        return arr


class Atom(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, argument: str) -> int:
        return Chemistry().names.index(get_atomic_name(argument)) + 1


class Bound(commands.Converter, int):
    def __init__(
        self, lower_bound: Optional[int] = None, upper_bound: Optional[int] = None
    ) -> None:
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        super().__init__()

    async def convert(self, ctx: Context, argument: int):
        if (
            self.lower_bound is not None and self.upper_bound is not None
        ):  # Both upper and lower bounds
            if argument < self.lower_bound or argument > self.upper_bound:
                raise ValueError(
                    f"Value not in bounds: {self.lower_bound} to {self.upper_bound}"
                )
            else:
                return argument
        elif (
            self.lower_bound is not None and self.upper_bound is None
        ):  # Just lower bound
            if argument < self.lower_bound:
                raise ValueError(f"Value not in bounds: at least {self.lower_bound}")
            else:
                return argument
        elif (
            self.lower_bound is None and self.upper_bound is not None
        ):  # Just upper bound
            if argument > self.upper_bound:
                raise ValueError(f"Value not in bounds: at most {self.upper_bound}")
            else:
                return argument
        else:  # No bounds on argument
            return argument


class GuildChannel(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, argument: str) -> discord.abc.GuildChannel:
        if ctx.guild is None:
            raise ScopeError("Cannot access a guild here")
        channels = ctx.guild.channels
        for chan in channels:
            if chan.name == argument:
                return chan
        else:
            raise ValueError("Cannot find channel with that name")


class UrlGet(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, url: str) -> commands.HybridCommand:
        if not (result := await find_url(url)):
            raise commands.errors.BadArgument("Invalid URL")
        try:
            res: aiohttp.ClientResponse = await ctx.bot.session.get(result[0])
        except aiohttp.InvalidURL:
            await asyncio.sleep(0)
            raise commands.errors.BadArgument("Invalid URL")
        except (
            aiohttp.client_exceptions.ClientConnectorCertificateError,
            aiohttp.client_exceptions.ClientConnectorError,
        ) as e:
            await asyncio.sleep(0)
            raise commands.errors.BadArgument(f"Invalid URL Endpoint: {e}")

        await asyncio.sleep(0)
        return res


class UrlFind(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, url: str) -> commands.HybridCommand:
        if not (result := await find_url(url)):
            raise commands.errors.BadArgument("Invalid URL")
        return result


class Cog(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, cog: str) -> commands.Cog:
        # cog = cog.capitalize()
        _cog: Optional[commands.Cog] = ctx.bot.get_cog(cog)
        if _cog is None:
            raise MissingCog(f"Cannot find cog: {cog}")
        if cog in Cogs.FORBIDDEN_COGS:
            raise ForbiddenData("Sorry! No help command is available for that.")
        return _cog


class Group(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, grp: str) -> commands.HybridGroup:
        # grp = grp.lower()
        _grp: Optional[commands.HybridGroup] = ctx.bot.get_command(grp)
        if _grp is None or not isinstance(_grp, commands.HybridGroup):
            raise MissingCog(f"Cannot find group: {grp}")
        if grp in Cogs.FORBIDDEN_GROUPS:
            raise ForbiddenData("Sorry! No help command is available for that.")
        return _grp


class Command(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, command: str) -> commands.HybridCommand:
        _command: Optional[
            Union[commands.HybridCommand, commands.Command]
        ] = ctx.bot.get_command(command)
        if _command is None:
            raise MissingCommand(f"Cannot find command: {command}")
        if command in Cogs.FORBIDDEN_COMMANDS:
            raise ForbiddenData("Sorry! No help command is available for that.")
        return _command


class RGB(commands.Converter):
    __name__ = "RBGA"

    def __init__(self, alpha: bool = True, alpha_default: int = 255) -> None:
        self.alpha: bool = alpha
        self.alpha_default: int = alpha_default
        super().__init__()

    async def convert(self, ctx: Context, value: str) -> np.ndarray:
        value = value.strip(" ,.").replace(" ", "")
        values = value.split(",")
        values = np.array(values, dtype=int)
        if self.alpha:
            if len(values) == 3:
                av = list(values)
                av.append(self.alpha_default)
                values = np.array(av)
            elif len(values) != 4:
                raise ValueError(
                    f"Invalid amount of colors given, expected 3 or 4. Got: {len(values)}"
                )
        else:
            if len(values) != 3:
                raise ValueError(
                    f"Invalid amount of colors given, expected 3. Got: {len(values)}"
                )
        if np.any(values[(values > 255) | (values < 0)]):
            raise ValueError("Value given is either greater an 255 or less than 0")
        return values


def getCastable(item: object, target: type):
    try:
        return target(item)
    except TypeError:
        return None


class ColorChannelConverterNoAlpha(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, argument: str) -> Set[int]:
        conversion_dict = {"R": 0, "G": 1, "B": 2}
        argument = argument.upper()
        for x in argument:
            if x not in conversion_dict.keys():
                raise ValueError("Invalid channel(s) given")
        return {conversion_dict.get(chan) for chan in argument}


class ColorChannelConverterAlpha(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, argument: str) -> Set[int]:
        conversion_dict = {"R": 0, "G": 1, "B": 2, "A": 3}
        argument = argument.upper().replace(" ", "")
        for x in argument:
            if x not in conversion_dict.keys():
                raise ValueError("Invalid channel(s) given")
        return {conversion_dict.get(chan) for chan in argument}


class CodeBlock(commands.Converter):
    async def convert(self, ctx, block: str):
        lines = block.split("\n")
        if "```" in lines[0]:
            lines.pop(0)
        if "```" in lines[len(lines) - 1]:
            lines.pop(len(lines) - 1)
        return "\n".join(lines)
