import aiohttp
import asyncio
import asyncpg
import discord
import logging
import openai
import time

from multiprocessing import freeze_support
from discord.ext import commands
from typing import Iterable, Mapping, Union

from selenium.webdriver import Chrome

from src.utils.startup_functions import (
    do_prep,
    startup_print,
)
from data.environ import APPLICATION_ID, BOT_KEY, OPENAI_KEY
from src.utils.types import Caches
from data.settings import PREFIXES

# Logging ---------------------------------------------------
logger: logging.Logger = logging.getLogger("discord")
logger.setLevel(logging.ERROR)

filename: str = "data\\logs\\_discord.log"
encoding: str = "UTF-8"
mode: str = "w"

handler: logging.FileHandler = logging.FileHandler(
    filename=filename, encoding=encoding, mode=mode
)
formatter: logging.Formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
# -----------------------------------------------------------


class Builder(commands.Bot):
    def __init__(self):
        command_prefix: Iterable[str] = PREFIXES
        help_command: Union[commands.HelpCommand, None] = None
        tree_cls: type = BuilderTree
        intents: discord.Intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        application_id: str = APPLICATION_ID
        case_insensitive: bool = True

        super().__init__(
            command_prefix=command_prefix,
            help_command=help_command,
            tree_cls=tree_cls,
            intents=intents,
            application_id=application_id,
            case_insensitive=case_insensitive,
        )
        self.openai: openai = openai
        self.openai.api_key = OPENAI_KEY

        self.start_unix: float = time.time()

        self.apg: asyncpg.Connection
        self.caches: Caches
        self.driver: Chrome
        self.session: aiohttp.ClientSession
        self.tree: BuilderTree

    async def setup_hook(self) -> None:
        await startup_print(self)


class BuilderContext(commands.Context):
    def __init__(self, **data):
        self.bot: Builder = data["bot"]
        super().__init__(**data)


class BuilderTree(discord.app_commands.CommandTree):
    def __init__(self, client: discord.Client):
        super().__init__(client, fallback_to_global=True)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.type != discord.InteractionType.application_command:
            return True

        default: Mapping[str, bool] = {"defer": True, "thinking": True, "ephemeral": False}
        settings: Mapping[str, bool] = getattr(
            interaction.command.callback, "defer", default
        )
        if settings["defer"]:
            try:
                await interaction.response.defer(
                    thinking=settings["thinking"], ephemeral=settings["ephemeral"]
                )
            except discord.NotFound:
                pass
        for name, param in interaction.command._params.items():
            if param.type == discord.AppCommandOptionType.attachment:
                obj: discord.Attachment = getattr(interaction.namespace, name)
                if obj.size > 2 ** 22: # ~4MB
                    raise commands.errors.BadArgument("Image is too large.")
        return True


async def main():
    bot: Builder = Builder()
    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
        },  # :troll:
    ) as bot.session:
        bot = await do_prep(bot)
        await bot.start(BOT_KEY)


if __name__ == "__main__":
    freeze_support()
    asyncio.run(main())
