import discord
from discord.ext import commands

import math
from typing import Iterable, Mapping, Optional
from src.cogs.development.Watchers import Watchers

from src.auxiliary.user.Embeds import fmte_i
from src.auxiliary.bot.Constants import CONSTANTS


class Paginator(discord.ui.View):
    def __init__(self, ctx: commands.Context, values: Iterable, pagesize: int, *,
                 timeout: Optional[float] = 45):
        self.ctx = ctx
        self.pagesize = pagesize

        self.position = 1

        self.vals = values
        self.message: Optional[discord.Message] = None
        
        self.maxpos = math.ceil((len(self.vals) / pagesize))

        super().__init__(timeout=timeout)

    @discord.ui.button(emoji=CONSTANTS.Emojis().BBARROW_ID, custom_id="bb")
    async def fullback(self, inter: discord.Interaction, button: discord.ui.Button):
        self.position = 1
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=CONSTANTS.Emojis().BARROW_ID, custom_id="b")
    async def back(self, inter: discord.Interaction, button: discord.ui.Button):
        self.position -= 1
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=":x:", style=discord.ButtonStyle.red, custom_id="x")
    async def close(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        await inter.message.delete()

    @discord.ui.button(emoji=CONSTANTS.Emojis().FARROW_ID, custom_id="f")
    async def next(self, inter: discord.Interaction, button: discord.ui.Button):
        self.position += 1
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=CONSTANTS.Emojis().FFARROW_ID, custom_id="ff")
    async def fullnext(self, inter: discord.Interaction, button: discord.ui.Button):
        self.position = self.maxpos
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    def embed(self, inter: discord.Interaction):
        """
        Should be overwritten to provide custom labeling
        ```py
        def embed(self, inter: discord.Interaction):
        ```
        """
        return fmte_i(
            inter,
            t=f"Pages: `{self.position}` of `{self.maxpos}`"
        )

    def add_fields(self, embed: discord.Embed):
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

    def page_zero(self, interaction: discord.Interaction):
        self.position = 1
        return self.add_fields(self.embed(interaction))

    def checkButtons(self, button: discord.Button = None):
        """
        Can be overwritten if necessary.
        """
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
        for b in [c for c in self.children if isinstance(
                c, discord.ui.Button) and c.custom_id != "x"]:
            if b == button:
                b.style = discord.ButtonStyle.success
            else:
                b.style = discord.ButtonStyle.secondary

    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True
        if self.message is None:
            raise commands.errors.MissingRequiredArgument("bozo you forgor to add the message to the view, imagine")
        await self.message.edit(view=self)

class AutoModal(discord.ui.Modal):
    def __init__(self, *, title: str, timeout: Optional[float] = None, custom_id: str = None) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)\
        if custom_id else\
        super().__init__(title=title, timeout=timeout)

    
    async def on_error(self, interaction: discord.Interaction, error: Exception, ) -> None:
        return await Watchers.handle_modal_error(interaction, error)