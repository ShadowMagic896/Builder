from codecs import ignore_errors
from importlib.resources import path
import os
from typing import Callable, Iterable, Literal, Optional, Tuple, List, Mapping, Any
import typing
import discord

from discord.ext import commands
def GIE(d: Mapping[Any, Any], k: Any, default: Optional[Any] = None):
    return d[k] if k in d else default

async def load_extensions(bot: commands.Bot, extension_paths: Iterable[str], **opts) -> str:
    """
    bot: Yout bot. Send when calling this command in your main
    logging: Whether to return the log of successes / failues after loading cogs. Will not print if ignore_errors is False and an error is encountered.
    """
    log: str = ""

    # Is this just getattr? idk
    GIE: Callable[[dict, Literal, type, Any]] = lambda mapping, key, expected_type, default: mapping[key] if key in mapping and type(mapping[key]) == expected_type else default
    spaces: int = GIE(opts, "spaces", int,  15)
    ignore: bool = GIE(opts, "ignore_errors", bool, True)

    files: List[Tuple[str, List[str]]] = []
    [
        files.extend([(
            path.replace("/", ".").strip("./_"), 
            os.listdir(path)
        )]) 
        for path in extension_paths
    ]

    for source, cogs in files:
        for cog in cogs:
            exp = " " * max(0, spaces - len(cog))
            if cog.startswith("_") or not cog.endswith(".py"): continue
            try:
                await bot.load_extension(f"{source}.{cog[:-3]}")

            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                await bot.load_extension(f"cogs.{cog[:-3]}")
            
            except BaseException as e:
                if ignore:
                    raise e
                log += f"❌ {cog} {exp} [{source}.{cog[:-3]}] [{str(e)[str(e).index(':')+2:]}]\n"
                continue

            log += f"✅ {cog} {exp} [{source}.{cog[:-3]}]\n"

    return log
