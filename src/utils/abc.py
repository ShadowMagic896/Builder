import logging
import math
from typing import Any, Coroutine, Generic, Optional, Sequence, TypeVar

import discord
from discord.app_commands import errors as app_errors
from discord.ext import commands

from .bot_types import Builder, BuilderContext
from .constants import Emojis
from .error_funcs import _interaction_error_handler, handle_modal_error

SequenceT = TypeVar("SequenceT", bound=Sequence)


class BaseCog(commands.Cog):
    def __init__(self, bot: Builder) -> None:
        self.bot: Builder = bot
        super().__init__()

    def ge(self) -> str:
        return "\N{Black Question Mark Ornament}"

    async def cog_load(self) -> None:
        logging.debug(f"Cog Loaded: {self.__class__.__module__}")

    async def cog_unload(self) -> None:
        logging.debug(f"Cog Unloaded: {self.__class__.__module__}")

    async def cog_command_error(
        self, ctx: BuilderContext[Builder], error: Exception
    ) -> None:
        return await _interaction_error_handler(ctx.interaction, error)

    async def cog_check(self, ctx: BuilderContext[Builder]) -> bool:
        return True


class BaseView(discord.ui.View):
    def __init__(
        self,
        ctx: BuilderContext,
        timeout: Optional[float] = 900,
    ):
        self.message: discord.Message = None
        self.ctx = ctx
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return all(
            [
                self.ctx.author == interaction.user,
                self.ctx.channel == interaction.channel,
                not interaction.user.bot,
            ]
        )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception, item: Any
    ) -> None:
        if isinstance(error, app_errors.CheckFailure):
            return await interaction.response.send_message(
                f"This isn't your message!\nYou can create your own with `{interaction.command}`"
            )
        return await _interaction_error_handler(interaction, error)

    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True
        try:
            await self.message.edit(view=self)
        except (discord.NotFound, AttributeError):
            pass


class Paginator(BaseView, Generic[SequenceT]):
    def __init__(
        self,
        ctx: BuilderContext,
        values: SequenceT,
        pagesize: int,
        *,
        timeout: Optional[float] = 45,
    ):
        self.ctx = ctx
        self.pagesize = pagesize

        self.position = 0

        self.values = values
        self.message: Optional[discord.Message] = None

        self.maxpos = math.ceil((len(self.values) / pagesize)) - 1
        self.start, self.stop = 0, pagesize

        super().__init__(ctx, timeout=timeout)

    @discord.ui.button(emoji=Emojis.BBARROW_ID, custom_id="bb", row=0)
    async def fullback(
        self, inter: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.position = 0
        await self.update(button)

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=Emojis.BARROW_ID, custom_id="b", row=0)
    async def back(self, inter: discord.Interaction, button: discord.ui.Button) -> None:
        self.position -= 1
        await self.update(button)

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        emoji="\N{CROSS MARK}", style=discord.ButtonStyle.red, custom_id="x", row=0
    )
    async def close(
        self, inter: discord.Interaction, button: discord.ui.Button
    ) -> None:
        for c in self.children:
            c.disabled = True
        try:
            await inter.response.edit_message(view=self)
        except (discord.NotFound, AttributeError):
            pass
        super().stop()

    @discord.ui.button(emoji=Emojis.FARROW_ID, custom_id="f", row=0)
    async def next(self, inter: discord.Interaction, button: discord.ui.Button) -> None:
        self.position += 1
        await self.update(button)

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=Emojis.FFARROW_ID, custom_id="ff", row=0)
    async def fullnext(
        self, inter: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.position = self.maxpos
        await self.update(button)

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.select(custom_id="page_selector", min_values=1, max_values=1, placeholder="Select Page", options=[], row=1) # Options are set in .update(), which is called before the view is sent
    async def page_selector(
        self, inter: discord.Interaction, select: discord.ui.Select
    ) -> None:
        self.position = int(select.values[0])
        await self.update()

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    async def embed(self, inter: discord.Interaction) -> discord.Embed:
        """
        Should be overwritten to provide custom labeling
        """
        return await self.ctx.format(
            title=f"Pages: `{self.position+1}` of `{self.maxpos or 1}`"
        )

    async def adjust(self, embed: discord.Embed) -> discord.Embed:
        return embed

    async def page_zero(
        self, interaction: discord.Interaction
    ) -> discord.Embed:
        self.position = 0
        return await self.adjust(await self.embed(interaction))

    async def update(self, button: discord.Button = None) -> None:
        """
        Can be overwritten if necessary.
        """
        options = [
            discord.SelectOption(
                label=f"Page: {page+1}" if page != self.position else f"Page: {page+1} [Current]",
                value=page
            ) for page in range(
                max(self.position-12, 0), min(self.position+12+1, self.maxpos+1) # Account for the current page
            )
        ] or [
            discord.SelectOption(label=f"Page: 1 [Current]", value=1)
        ]

        # Find the page selector and update its options
        for child in self.children:
            if isinstance(child, discord.ui.Select) and child.custom_id == "page_selector":
                child.options = options


        if self.maxpos <= 0:
            for b in self.children:
                if isinstance(b, discord.ui.Button) and b.custom_id != "x":
                    b.disabled = True
                    b.style = discord.ButtonStyle.grey
        else:
            if self.position == 0:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("b", "bb"):
                            b.disabled = True
            else:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("b", "bb"):
                            b.disabled = False
            if self.position == self.maxpos:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("f", "ff"):
                            b.disabled = True
            else:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("f", "ff"):
                            b.disabled = False
        if button is None:
            return
        for b in [
            c
            for c in self.children
            if isinstance(c, discord.ui.Button) and c.custom_id != "x"
        ]:
            if b == button:
                b.style = discord.ButtonStyle.success
            else:
                b.style = discord.ButtonStyle.secondary

    @property
    def value_start(self) -> int:
        return self.pagesize * (self.position)

    @property
    def value_stop(self) -> int:
        return self.pagesize * (self.position + 1)

    @property
    def value_range(self) -> SequenceT:
        return self.values[self.value_start : self.value_stop]

    @property
    def position_absoloute(self) -> int:
        return self.position * self.pagesize

    def format_absoloute(self, offset: int) -> str:
        return str(self.position_absoloute + offset + 1).rjust(3, "0")


class BaseModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        title: str = discord.utils.MISSING,
        timeout: Optional[float] = None,
        custom_id: str = discord.utils.MISSING,
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
    ) -> None:
        return await handle_modal_error(interaction, error)
