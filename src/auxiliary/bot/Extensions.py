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
    log: str = ""

    spaces: int = opts.get("spaces", 15)
    ignore: bool = opts.get("ignore_errors", True)

    files: List[Tuple[str, List[str]]] = [
        (path.replace("/", ".").strip("./_"), os.listdir(path))
        for path in extension_paths
    ]

    for source, cogs in files:
        for cog in cogs:
            exp = " " * max(0, spaces - len(cog))
            if cog.startswith("_") or not cog.endswith(".py"): continue
            try:
                await bot.load_extension(f"{source}.{cog[:-3]}")

            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                await bot.load_extension(f"{source}.{cog[:-3]}")
            
            except BaseException as e:
                if not ignore:
                    raise e
                log += f"\N{CROSS MARK} {cog} {exp} [{source}.{cog[:-3]}] [{str(e)[str(e).index(':')+2:]}]\n"
                continue

            log += f"\N{WHITE HEAVY CHECK MARK} {cog} {exp} [{source}.{cog[:-3]}]\n"

    return log