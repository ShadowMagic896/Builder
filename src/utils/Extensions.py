from glob import glob, iglob
import os
import pathlib
from pathlib import Path
from typing import Iterable, Optional, Tuple, List, Mapping, Any
import discord

from data.settings import NOLOAD_EXTS


def GIE(d: Mapping[Any, Any], k: Any, default: Optional[Any] = None):
    return d[k] if k in d else default

def format_path(path: str):
    return (path.replace(os.getcwd(), ".") + "\\").replace("\\", ".").strip(".").removesuffix(".py")

async def load_extensions(bot: Any, ext_dirs: Iterable[Path], **opts) -> str:
    ignore: bool = opts.get("ignore_errors", True)

    files = []
    for path in ext_dirs:
        path = Path(path).absolute()
        files.extend(
            [
                format_path(p) for p in iglob(f"{path}/**/*.py", recursive=True)
            ]
        )

    for path in files:
        if path in NOLOAD_EXTS:
            continue
        if path.startswith("_"):
            continue
        print(path)
        try:
            await bot.load_extension(path)

        except discord.ext.commands.errors.ExtensionAlreadyLoaded:
            await bot.reload_extension(path)

        except BaseException as e:
            if not ignore:
                raise e