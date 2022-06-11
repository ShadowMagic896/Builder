from typing import List
import discord
from discord.ext import commands
import re

from src.utils.Functions import explode
from src.utils.Constants import CONSTANTS
from bot import BuilderContext


def iototime(userinput: str):
    t = userinput

    def e(l: list):
        for r in l:
            if t.endswith(r):
                return True
        return False

    def findLimit(input):
        for c, char in enumerate(t):
            try:
                int(char)
            except BaseException:
                break
        return int(c)

    if any([e(["s", "sec", "secs", "second", "seconds"])]):
        return int(t[: findLimit(t)])

    elif any([e(["m", "min", "mins", "minute", "minutes"])]):
        return int(t[: findLimit(t)]) * 60

    elif any([e(["h", "hr", "hrs", "hour", "hours"])]):
        return int(t[: findLimit(t)]) * 60 * 60

    elif any([e(["d", "ds", "day", "days"])]):
        return int(t[: findLimit(t)]) * 60 * 60 * 24

    elif any([e(["w", "wk", "wks", "week", "weeks"])]):
        return int(t[: findLimit(t)]) * 60 * 60 * 24 * 7

    else:
        return 60 * 60  # Not sure what they meant, so just do an hour.


async def actual_purge(ctx: BuilderContext, limit, user: discord.Member = None):
    errors = 0
    dels = 0
    async for m in ctx.channel.history(limit=round((limit + 10) * 1.5)):
        # if there is a user, care, otherwise just go on ahead
        if m.author == user if user else True:
            try:
                await m.delete()
            except discord.errors.Forbidden or discord.errors.NotFound:
                errors += 1
            dels += 1
        if dels == limit:
            break
    return (dels, errors)


def clean(_input: str):
    banned_chars = [";", '"', "'"]
    for r in _input:
        if r in banned_chars:
            raise commands.errors.BadArgument(_input)
    for c in _input:
        try:
            c.encode("utf-8")
        except UnicodeEncodeError:
            raise commands.errors.BadArgument(_input)


def convCodeBlock(code: str):
    match = "```.*[\n]?[^```]+```"
    se = re.search(match, code.strip())
    if not se:
        raise commands.errors.BadArgument("Invalid code format.")
    return se.group()


async def cogAutocomplete(
    bot: commands.Bot, inter: discord.Interaction, current: str
) -> List[discord.app_commands.Choice[str]]:
    return sorted(
        [
            discord.app_commands.Choice(name=c, value=c)
            for c in list(bot.cogs.keys())
            if ((current.lower() in c.lower() or (c.lower()) in current.lower()))
            and c not in CONSTANTS.Cogs().FORBIDDEN_COGS
        ][:25],
        key=lambda c: c.name,
    )


async def groupAutocomplete(
    bot: commands.Bot, inter: discord.Interaction, current: str
) -> List[discord.app_commands.Choice[str]]:
    return (
        sorted(
            [
                discord.app_commands.Choice(
                    name=g.qualified_name, value=g.qualified_name
                )
                for g in bot.commands
                if isinstance(g, commands.HybridGroup)
                and (
                    g.qualified_name.lower() in current.lower()
                    or current.lower() in g.qualified_name.lower()
                )
            ][:25],
            key=lambda c: c.name,
        )
        if (cog := getattr(inter.namespace, "cog", None)) is None
        else sorted(
            [
                discord.app_commands.Choice(
                    name=g.qualified_name, value=g.qualified_name
                )
                for g in bot.commands
                if isinstance(g, commands.HybridGroup)
                and (
                    g.cog is not None
                    and (
                        g.qualified_name.lower() in current.lower()
                        or current.lower() in g.qualified_name.lower()
                    )
                )
                and g.cog_name.lower() == cog.lower()
            ][:25],
            key=lambda c: c.name,
        )
    )


async def commandAutocomplete(
    bot: commands.Bot, inter: discord.Interaction, current: str
) -> List[discord.app_commands.Choice[str]]:
    return sorted(
        [
            discord.app_commands.Choice(
                name="[{}] {}".format(c.cog_name, c.qualified_name),
                value=c.qualified_name,
            )
            for c in (
                explode([c for c in bot.commands])
                if not getattr(inter.namespace, "cog")
                else explode(
                    bot.get_cog(inter.namespace.cog).get_commands()
                    if (bot.get_cog(inter.namespace.cog)) is not None
                    or inter.namespace.cog in CONSTANTS.Cogs().FORBIDDEN_COGS
                    else []
                )
                if inter.namespace.cog in [c for c, _ in bot.cogs.items()]
                else []
            )
            if (
                (current.lower() in c.qualified_name.lower())
                or (c.qualified_name.lower() in current.lower())
            )
            and c.cog_name not in CONSTANTS.Cogs().FORBIDDEN_COGS
        ][:25],
        key=lambda c: c.name[c.name.index("]") + 1 :],
    )


async def guildChannelAutoComplete(inter: discord.Interaction, current: str):
    return [
        discord.app_commands.Choice(
            name=f"{type(chan).__name__}: {chan.name}", value=chan.name
        )
        for chan in inter.guild.channels
        if chan.name.lower() in current.lower() or current.lower() in chan.name.lower()
    ]
