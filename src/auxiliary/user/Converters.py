from typing import List, Optional, Type
import discord
from discord.ext import commands
from discord.ext.commands import Context
from data.ItemMaps import Chemistry, getAtomicName
import re


class UserConverter(commands.Converter):
    async def convert(self, ctx: Context, user: str):
        if not user:
            raise commands.errors.UserNotFound(user)
        _id = None
        if user.startswith("<@"):  # User is a mention
            try:
                _id = int(str(user)[2:-1])
            except ValueError:
                raise commands.errors.UserNotFound(user)
        else:  # It is a user ID
            try:
                _id = int(user)  # Just an ID
            except ValueError:
                for m in ctx.guild.members:  # Try to catch a name
                    if (
                        m.name == user
                        or "{}#{}".format(m.name, m.discriminator) == user
                    ):
                        _id = m.id
                else:
                    commands.errors.UserNotFound(user)
        try:
            users = []
            for r in ctx.bot.guilds:
                for m in r.members:
                    users.append(m)

            return discord.utils.find(lambda u: u.id == _id, users)
        except discord.errors.NotFound:
            raise commands.errors.UserNotFound(user)


class YouTubeLink(commands.Converter):
    async def convert(self, ctx: Context, arg: str):
        match = "(http(s)?://)?(www.)?youtube.com/watch\\?v=.+"

        if not re.match(match, arg):
            raise commands.errors.BadArgument("Invalid URL")

        if not arg.startswith("https://"):
            arg = "https://" + arg

        arg = arg.replace("www.", "")

        if not re.match(match, arg):
            raise commands.errors.BadArgument("Invalid URL: %s" % arg)

        return arg


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

    def strToList(self, string: str, convtype: Type) -> List[int]:
        return [
            self.convtype(a)
            for a in string.replace("[", "")
            .replace("]", "")
            .replace(" ", "")
            .split(",")
        ]


class Atom(commands.Converter):
    def __init__(self) -> None:
        super().__init__()

    async def convert(self, ctx: Context, argument: str) -> int:
        return Chemistry().names.index(getAtomicName(argument)) + 1


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


# L
