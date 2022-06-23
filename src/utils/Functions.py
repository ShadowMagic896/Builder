import asyncio
from asyncio.subprocess import PIPE, Process
import re
import discord
from discord.ext import commands
import inspect
import os
from typing import List


from importlib import import_module


def explode(l: List[commands.HybridCommand]) -> List[commands.HybridCommand]:
    for c in list(l):
        if hasattr(c, "commands"):
            for v in explode(c.commands):
                yield v
        else:
            # if isinstance(c, commands.):
            #     continue # ignore text commands, just dev stuff
            yield c


def fmtDict(d: dict):
    """
    Formats a dictionary to be placeable into a PostgreSQL DB.
    """
    return str(d).replace("'", '"')


async def add_cog_loaders(bot: commands.Bot, paths: List[os.PathLike]):
    for dir_ in paths:
        if dir_.startswith("_"):
            continue
        for file in os.listdir(dir_):
            if file.startswith("_"):
                continue
            _formatted = file.replace("/", "\\")
            fullname = f"{dir_.replace('.', '')}\\{_formatted}".replace(
                "/", "."
            ).replace("\\", ".")
            await _add_cog_loaders(bot, fullname)


async def _add_cog_loaders(bot: commands.Bot, filename: os.PathLike):
    """
    Automatically adds all cog classes to the bot from a given file.
    """
    module = import_module(filename[1:-3])  # Remove the "." and ".py"
    # A list of all cog classes defined in the file
    cogs: List[commands.Cog] = []

    # Get all classes in the file
    classes = inspect.getmembers(module, inspect.isclass)

    for name, class_ in classes:
        if discord.ext.commands.cog.Cog in class_.__mro__:
            print(f"Add class: {name}")
            cogs.append(class_)

    for cog in cogs:
        print(f"COG: {cog.qualified_name()}")
        await bot.add_cog(cog(bot))


async def format_code():
    proc: Process = await asyncio.create_subprocess_shell(f"py -m black .", stdout=PIPE)
    await proc.communicate()


async def find_url(url: str):
    if not url.startswith("http"):
        url = f"https://{url}"
    regex = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    return regex.findall(url)


async def filter_similar(values, req_ratio, req_diff):
    # this is kinda a cheap way of doing it. For example, (255, 0, 0) will get discarded if (0, 0, 255) exists
    # It just saves a signifgant amount of time, and I honestly don't want to write all of the required NumPy stuff to do this properly
    # Besides, having two start constasts like that is probably uncommon, and
    # a small change like (1, 0, 255) can change it totally.
    for co, val in enumerate(values):
        deleted: int = 0
        for xco, xval in enumerate(values[co + 1 :], start=co + 1):
            similar: int = 0
            for channel in range(3):
                ab_diff = abs(val[channel] - xval[channel])
                ab_ratio = abs(1 - ((val[channel] or 1) / (xval[channel] or 1)))
                if ab_diff < req_diff or ab_ratio < req_ratio:
                    similar += 1
            if similar > 1:
                del values[xco - deleted]
                deleted += 1
    return values
