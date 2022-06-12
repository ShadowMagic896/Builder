import discord
from discord.ext import commands
from discord.app_commands import errors as app_errors

import math
from typing import Any, List, Optional, Type
from src.cogs.development.ErrorHandling import ErrorHandling

from src.utils.Embeds import fmte_i
from src.utils.Constants import CONSTANTS
from bot import BuilderContext


class BaseView(discord.ui.View):
    """
    This is the base view that automatically implements `interaction_check`, `on_error`, & `on_timeout` with
    basic solutions. Designed to help not repeat code. All views should inherit from this.
    """

    def __init__(
        self,
        ctx: BuilderContext,
        timeout: Optional[float] = 300,
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
        return await ErrorHandling(self.ctx.bot)._interaction_error_handler(
            interaction, error
        )

    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True
        try:
            await self.message.edit(view=self)
        except (discord.NotFound, AttributeError):
            pass


class Paginator(BaseView):
    def __init__(
        self,
        ctx: BuilderContext,
        values: List,
        pagesize: int,
        *,
        timeout: Optional[float] = 45,
    ):
        self.ctx = ctx
        self.pagesize = pagesize

        self.position = 1

        self.vals: List[Type[values]] = values
        self.message: Optional[discord.Message] = None

        self.maxpos = math.ceil((len(self.vals) / pagesize))
        self.start, self.stop = 0, pagesize

        super().__init__(ctx, timeout=timeout)

    @discord.ui.button(emoji=CONSTANTS.Emojis().BBARROW_ID, custom_id="bb")
    async def fullback(self, inter: discord.Interaction, button: discord.ui.Button):
        self.position = 1
        await self.checkButtons(button)

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=CONSTANTS.Emojis().BARROW_ID, custom_id="b")
    async def back(self, inter: discord.Interaction, button: discord.ui.Button):
        self.position -= 1
        await self.checkButtons(button)

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        emoji="\N{CROSS MARK}", style=discord.ButtonStyle.red, custom_id="x"
    )
    async def close(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.message.delete()

    @discord.ui.button(emoji=CONSTANTS.Emojis().FARROW_ID, custom_id="f")
    async def next(self, inter: discord.Interaction, button: discord.ui.Button):
        self.position += 1
        await self.checkButtons(button)

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=CONSTANTS.Emojis().FFARROW_ID, custom_id="ff")
    async def fullnext(self, inter: discord.Interaction, button: discord.ui.Button):
        self.position = self.maxpos
        await self.checkButtons(button)

        embed = await self.adjust(await self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    async def embed(self, inter: discord.Interaction):
        """
        Should be overwritten to provide custom labeling
        """
        return fmte_i(inter, t=f"Pages: `{self.position}` of `{self.maxpos or 1}`")

    async def adjust(self, embed: discord.Embed):
        """
        This must be overwritten by inheriting classes.
        Should return an embed with self.pagesize fields. Example:

        ```py
        #------------------------------------------------------------------

        start = self.pagesize * (self.position - 1)
        stop = self.pagesize * self.position

        values = self.vals[start:stop]
        # In this scenario, 'values' is a list of tups of (user, integer)

        for count, entry in enumerate(values):
            user, bal = entry
            place = count + 1 + (self.pos - 1) * self.pagesize # Account for shifting if this is not the first page.

            embed.add_field(
                name=f"{place}: {user}",
                value=f"`{bal}`",
                inline=False
            )
        return embed
        #------------------------------------------------------------------
        ```
        """
        return embed

    async def page_zero(self, interaction: discord.Interaction):
        self.position = 1
        return await self.adjust(await self.embed(interaction))

    async def checkButtons(self, button: discord.Button = None):
        """
        Can be overwritten if necessary.
        """
        self.start = self.pagesize * (self.position - 1)
        self.start = self.pagesize * self.position
        if self.maxpos <= 1:
            for b in self.children:
                if isinstance(b, discord.ui.Button) and b.custom_id != "x":
                    b.disabled = True
                    b.style = discord.ButtonStyle.grey
        else:
            if self.position == 1:
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


class BaseModal(discord.ui.Modal):
    def __init__(
        self, *, title: str, timeout: Optional[float] = None, custom_id: str = None
    ) -> None:
        super().__init__(
            title=title, timeout=timeout, custom_id=custom_id
        ) if custom_id else super().__init__(title=title, timeout=timeout)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
    ) -> None:
        return await ErrorHandling.handle_modal_error(interaction, error)