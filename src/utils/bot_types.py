import time

import aiohttp
import asyncpg
import datetime
import discord
import logging
import openai
from discord.ext import commands
from environ import APPLICATION_ID, OPENAI_KEY
from settings import BLACKLIST_USERS, PREFIXES
from typing import Generic, Iterable, Mapping, Optional, TypeVar, Union
from webbrowser import Chrome

from .extensions import full_reload
from .types import Cache


_Bot = Union[commands.Bot, commands.AutoShardedBot]
BotT = TypeVar("BotT", bound=_Bot, covariant=True)


class Builder(commands.Bot):
    def __init__(self):
        command_prefix: Iterable[str] = PREFIXES
        help_command: Optional[commands.HelpCommand] = None
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
        self.caches: Cache
        self.driver: Chrome
        self.session: aiohttp.ClientSession
        self.tree: BuilderTree

    async def reload_source(self) -> str:
        return await full_reload(self)

    async def setup_hook(self) -> None:
        print("--- online ---")


class BuilderContext(commands.Context, Generic[BotT]):
    def __init__(self, **data):
        self.bot: Builder = data["bot"]
        super().__init__(**data)


class BuilderTree(discord.app_commands.CommandTree):
    def __init__(self, client: discord.Client):
        super().__init__(client, fallback_to_global=True)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.type == discord.InteractionType.application_command:
            default: Mapping[str, bool] = {
                "defer": True,
                "thinking": True,
                "ephemeral": False,
            }
            settings: Mapping[str, bool] = getattr(
                interaction.command.callback, "defer", default
            )
            if settings["defer"]:
                try:
                    await interaction.response.defer(
                        thinking=settings["thinking"], ephemeral=settings["ephemeral"]
                    )
                except (discord.NotFound, discord.InteractionResponded):
                    logging.error("Message not found for deferring")
            for name, param in interaction.command._params.items():
                if param.type == discord.AppCommandOptionType.attachment:
                    obj: discord.Attachment = getattr(interaction.namespace, name)
                    if obj.size > 2**22:  # ~4MB
                        raise commands.errors.BadArgument("Image is too large.")
        return interaction.user not in BLACKLIST_USERS
