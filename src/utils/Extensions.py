import discord
import importlib
import os
from discord.ext import commands
from glob import glob, iglob
from pathlib import Path
from settings import EXT_DIRECTORIES, NOLOAD_EXTS
from typing import Any, Iterable, Mapping, Optional


def GIE(d: Mapping[Any, Any], k: Any, default: Optional[Any] = None):
    return d[k] if k in d else default


def format_path(path: str):
    return (
        (path.replace(os.getcwd(), ".") + "\\")
        .replace("\\", ".")
        .strip(".")
        .removesuffix(".py")
    )


async def load_extensions(
    bot: Any, ext_dirs: Iterable[Path] = EXT_DIRECTORIES, **opts
) -> str:
    ignore: bool = opts.get("ignore_errors", True)

    files = []
    for path in ext_dirs:
        files.extend(extend_exts(path))

    for path in files:
        if path in NOLOAD_EXTS:
            continue
        if path.startswith("_"):
            continue
        try:
            await bot.load_extension(path)

        except discord.ext.commands.errors.ExtensionAlreadyLoaded:
            await bot.reload_extension(path)

        except BaseException as e:
            if not ignore:
                raise e


def extend_exts(path: str):
    def format_path(path: str):
        return (
            (path.replace(os.getcwd(), ".") + "\\")
            .replace("\\", ".")
            .strip(".")
            .removesuffix(".py")
        )

    path = Path(path).absolute()
    return [format_path(p) for p in iglob(f"{path}/**/*.py", recursive=True)]


def extend_dir(path: str):
    path = Path(path).absolute()
    return glob(f"{path}/**/*.py", recursive=True)


def format_file(fn: str):
    _imp = fn.strip("./")[fn.index("src") :].replace("\\", ".")
    return _imp[:-3]

async def full_reload(bot: commands.Bot):
    log: str = ""
    for file in extend_dir("./src"):

        as_import = format_file(file)
        if as_import in bot.extensions.keys():
            log += f"\n**[EXT] {as_import}**"
            await bot.reload_extension(as_import)
        else:
            log += f"\n*[UTL] {as_import}*"
            module = importlib.import_module(as_import)
            importlib.reload(module)

    return log
