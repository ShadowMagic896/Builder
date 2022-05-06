# Hahha FUCK how many of these damned help commands wil I make?
from math import ceil, floor
from typing import Any, List, Optional
import discord
from discord import app_commands, Interaction
from discord.app_commands import describe
from discord.ext import commands

import os
from _aux.embeds import Desc, fmte, fmte_i
from archived_cogs.InterHelp import CogSelect


class MixedHelp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    @describe(
        cog="The cog to view.",
        ephemeral=Desc.ephemeral
    )
    async def help(self, ctx: commands.Context, cog: Optional[str], ephemeral: bool = False):
        """
        Creates a menu to navigate all of the bot's commands
        """
        if cog is None:
            embed = fmte(
                ctx,
                t="Help",
                d="*%s*" % (await self.bot.application_info()).description
            )
            view = BaseView().add_item(CogSelect(self.bot, ctx, ephemeral))
            await ctx.send(embed=embed, view=view, ephemeral=ephemeral)
        else:
            cog: commands.Cog = self.bot.get_cog(cog)

            embed = CommandView(
                self.bot, ephemeral, cog, 5).page_zero(
                ctx.interaction)

            sel = CogSelect(self.bot, ctx, ephemeral)
            sel.placeholder = "%s Cog Selection..." % cog.ge()
            sel.options.remove(
                discord.utils.get(
                    sel.options,
                    label=cog.qualified_name))
            view = CommandView(self.bot, ephemeral, cog, 5).add_item(sel)
            view.checkButtons()

            await ctx.send(embed=embed, view=view)

    @help.autocomplete("cog")
    async def cog_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        return sorted([discord.app_commands.Choice(name=c, value=c) for c in list(self.bot.cogs.keys())if ((current.lower() in c.lower(
        ) or (c.lower()) in current.lower())) and c not in os.getenv("FORBIDDEN_COGS").split(";")][:25], key=lambda c: c.name)

    # @help.autocomplete("command")
    # async def command_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
    #     return sorted(
    #         [
    #             discord.app_commands.Choice(
    #                 name="[{}] {}".format(
    #                     c.cog_name, c.qualified_name), value=c.qualified_name) for c in (
    #                 self.explode([c for c in self.bot.commands]) if not getattr(
    #                     inter.namespace, "cog") else self.explode(self.bot.get_cog(
    #                         inter.namespace.cog).get_commands()) if inter.namespace.cog in [
    #                             c for c, v in self.bot.cogs.items()] else []) if (
    #                                 (current.lower() in c.qualified_name.lower()) or (
    #                                     c.qualified_name.lower() in current.lower())) and c.cog_name not in os.getenv("FORBIDDEN_COGS").split(";")][
    #                                         :25], key=lambda c: c.name[
    #                                             c.name.index("]") + 1:])

    async def main_embed(self, ctx: commands.Context, bot: commands.Bot):
        return fmte(
            ctx,
            t="Help",
            d="Hello there! {}\n**Cogs:** `{}`\n**Commands:** `{}`".format(
                (await self.bot.application_info()).description,
                len(self.bot.cogs),
                len(self.bot.commands)
            )
        )

    def explode(self, l: List[commands.HybridCommand]):
        """
        A recursive func to flatten all commands into one list
        """
        l = list(l)
        nl = []
        for c in l:
            if isinstance(c, (commands.HybridGroup, commands.Group,
                          app_commands.AppCommandGroup, app_commands.Group)):
                nl.extend(self.explode(c.commands))
            else:
                nl.append(c)
        return nl


class BaseView(discord.ui.View):
    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)


class CommandView(discord.ui.View):
    def __init__(self, bot: commands.Bot, ephemeral: bool, cog: commands.Cog,
                 pagesize: int, *, timeout: Optional[float] = 180):
        self.bot = bot
        self.ephemeral = ephemeral

        self.vals = sorted(
            MixedHelp(bot).explode(
                cog.get_commands()),
            key=lambda c: c.qualified_name)
        self.pos = 1
        self.maxpos = ceil((len(self.vals) / pagesize))
        self.pagesize = pagesize

        super().__init__(timeout=timeout)

    @discord.ui.button(emoji="<:BBArrow:971590922611601408> ", custom_id="bb")
    async def fullback(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos = 1
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:BArrow:971590903837913129>", custom_id="b")
    async def back(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos -= 1
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.red, custom_id="x")
    async def close(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.message.delete()

    @discord.ui.button(emoji="<:FArrow:971591003893006377>", custom_id="f")
    async def next(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos += 1
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:FFArrow:971591109874704455>", custom_id="ff")
    async def fullnext(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos = self.maxpos
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter,
            t="Commands: Page `{}` of `{}`".format(self.pos, self.maxpos)
        )

    def add_fields(self, embed: discord.Embed):
        for command in self.vals[self.pagesize *
                                 (self.pos - 1):self.pagesize * (self.pos)]:
            command: commands.HybridCommand = command
            # al = command.signature.split()
            embed.add_field(
                # name = "`/%s <%s params>`" % (command.qualified_name, len(al)),
                name="`/%s`" % command.qualified_name,
                # value = "*%s*\n`%s`" % (command.short_doc, command.signature),
                value="*%s*" % command.short_doc,
                inline=False
            )
        return embed

    def page_zero(self, interaction: Interaction):
        self.pos = 1
        return self.add_fields(self.embed(interaction))

    def checkButtons(self, button: discord.Button = None):
        if self.maxpos == 1:
            for b in self.children:
                if isinstance(b, discord.ui.Button) and b.custom_id != "x":
                    b.disabled = True
                    b.style = discord.ButtonStyle.grey
        else:
            if self.pos == 1:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("b", "bb"):
                            b.disabled = True
            else:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("b", "bb"):
                            b.disabled = False
            if self.pos == self.maxpos:
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


class CogSelect(discord.ui.Select):  # Shows all cogs in the bot
    def __init__(self, bot: commands.Bot,
                 context: commands.Context, ephemeral: bool):
        placeholder = "⚪ Cog Selection..."
        options = []

        self.bot = bot
        self.context = context
        self.ephemeral = ephemeral
        self.lastrem = None

        for name, cog in bot.cogs.items():
            if name in os.getenv("FORBIDDEN_COGS").split(";"):
                continue
            options.append(
                discord.SelectOption(
                    label=name,
                    description=cog.description,
                    emoji=cog.ge()
                )
            )
        super().__init__(
            placeholder=placeholder,
            options=options,
        )

    async def callback(self, interaction: Interaction) -> Any:
        opt = interaction.data["values"][0]
        obj = self.bot.get_cog(opt)
        self.placeholder = "%s Cog Selection..." % obj.ge()
        if self.lastrem:
            self.append_option(self.lastrem)
        self.lastrem = discord.utils.get(
            self.options, label=obj.qualified_name)
        self.options.remove(self.lastrem)
        self.options = sorted(self.options, key=lambda o: o.label)

        view = CommandView(self.bot, self.ephemeral, obj, 5)
        embed = view.page_zero(interaction)
        view.checkButtons()
        view.add_item(self)

        await interaction.response.edit_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(MixedHelp(bot))
