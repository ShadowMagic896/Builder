import datetime
import logging
import random
import time
import tkinter
from copy import copy
from enum import Enum
from typing import Generic, Mapping, Optional, TypeVar, Union
from webbrowser import Chrome

import aiohttp
import asyncpg
import discord
import openai
import pytenno
import wavelink
from discord.ext import commands

import settings_config_default as default
from environ import APPLICATION_ID, OPENAI_KEY
from settings import BLACKLIST_USERS

from .extensions import full_reload
from .types import Cache

_Bot = Union[commands.Bot, commands.AutoShardedBot]
BotT = TypeVar("BotT", bound=_Bot, covariant=True)


class BuilderContext(commands.Context, Generic[BotT]):
    def __init__(self, **data):
        super().__init__(**data)
        self.bot: Builder
        self.voice_client: BuilderWave | None

    async def format(
        self,
        title: str,
        desc: Optional[str] = None,
        color: discord.Color = discord.Color.teal(),
    ) -> discord.Embed:
        delay: str = f"{round(self.bot.latency, 3) * 1000}ms"
        author_name = str(self.author)
        author_url: str = f"https://discord.com/users/{self.author.id}"
        author_icon_url: str = self.author.display_avatar.url

        embed = discord.Embed(
            color=color,
            title=title,
            description=desc,
            type="rich",
            timestamp=datetime.datetime.now(),
        )
        embed.set_author(name=author_name, url=author_url, icon_url=author_icon_url)

        embed.set_footer(
            text=f"{self.message.content or self.prefix + self.command.qualified_name}  •  {delay}"
        )

        return embed


class Builder(commands.Bot):
    def __init__(self):
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
        self.cache: Cache
        self.cfdb: ConfigureDatabase
        self.driver: Chrome
        self.session: aiohttp.ClientSession
        self.tree: BuilderTree
        self.tkroot: tkinter.Tk
        self.tenno: pytenno.PyTenno
        self.wavelink: wavelink.NodePool

    async def reload_source(self) -> str:
        return await full_reload(self)

    async def setup_hook(self) -> None:
        print("--- online ---")

    async def get_context(
        self, origin: Union[discord.Message, discord.Interaction], *, cls=BuilderContext
    ) -> Union[commands.Context, BuilderContext]:
        return await super().get_context(origin, cls=cls)


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
            if interaction.command is None:
                return True
            settings: Mapping[str, bool] = getattr(
                interaction.command.callback, "defer", default
            )
            if settings["defer"]:
                try:
                    await interaction.response.defer(
                        thinking=settings["thinking"], ephemeral=settings["ephemeral"]
                    )
                except (discord.NotFound, discord.InteractionResponded):
                    logging.warning("Message not found for deferring")
            for name, param in interaction.command._params.items():
                if param.type == discord.AppCommandOptionType.attachment:
                    obj: discord.Attachment = getattr(interaction.namespace, name)
                    if obj is not None and obj.size > 2**22:  # ~4MB
                        raise commands.errors.BadArgument("Image is too large.")

        return interaction.user not in BLACKLIST_USERS

    async def format(
        self,
        title: str,
        desc: Optional[str] = None,
        color: discord.Color = discord.Color.teal(),
    ) -> discord.Embed | None:
        try:
            ctx = BuilderContext.from_interaction(self)
        except ValueError:
            return None
        return await ctx.format(title, desc, color)


class QueueType(Enum):
    default = 0
    shuffle = 1
    loop = 2


class BuilderWave(wavelink.Player):
    def __init__(self, ctx: BuilderContext, queue_type: QueueType):
        self.ctx = ctx
        self.queue_type = queue_type
        super().__init__()

    async def play_next(self) -> wavelink.Track | None:
        if self.queue.is_empty:
            return None
        if self.queue_type == QueueType.default:
            track = copy(self.queue[0])
            await self.play(track)
            del self.queue[0]
            return track
        elif self.queue_type == QueueType.loop:
            track = self.queue.get()
            await self.play(track)
            self.queue.put(track)
            return track
        elif self.queue_type == QueueType.shuffle:
            track = random.choice(self.queue)
            await self.play(track)
            self.queue.put(track)
            return track
        print("didn't do anything")
        return None


class ConfigureDatabase:
    def __init__(self, bot: Builder):
        self.bot = bot
        self.apg = bot.apg

    async def set_value(self, guild_id: int, key: str, value: str) -> None:
        command = """
            INSERT INTO config
            VALUES (
                $1, $2, $3   
            )
            ON CONFLICT (guildid, key) DO UPDATE
                SET value=$3
                WHERE config.guildid=$1 AND config.key=$2
        """
        await self.apg.fetchrow(command, guild_id, str(key), str(value))

    async def get_value(self, guild_id: int, key: str) -> str | None:
        command = """
            SELECT *
            FROM config
            WHERE guildid=$1 AND key=$2
        """
        return await self.apg.fetchrow(command, guild_id, str(key))


async def command_prefix(bot: Builder, message: discord.Message) -> str:
    query = """
        SELECT *
        FROM config
        WHERE guildid = $1 AND key = $2"""
    config = await bot.apg.fetchrow(query, message.guild.id, "prefix")
    if config is None:
        return default.PREFIX
    return config["value"]
