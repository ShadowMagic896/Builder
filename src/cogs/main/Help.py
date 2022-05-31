from inspect import _empty
import typing
import discord
from discord import Interaction, utils
from discord.app_commands import describe, Range
from discord.app_commands.transformers import CommandParameter
from discord.ext import commands

from math import ceil
from typing import Any, List, Optional, Union
from data.errors import ForbiddenData, MissingCog, MissingCommand

from src.auxiliary.user.Embeds import fmte, fmte_i
from src.auxiliary.user.UserIO import explode
from src.auxiliary.user.Subclass import BaseView, Paginator

from src.auxiliary.bot.Constants import CONSTANTS


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    @describe(
        cog="The cog to view",
        command="The command to view",
    )
    async def help(
        self, ctx: commands.Context, cog: Optional[str], command: Optional[str]
    ):
        """
        Creates a menu to navigate all of the bot's commands
        """
        if cog is None and command is None:  # Send main help
            embed = fmte(
                ctx,
                t="Help",
                d="*%s*" % (await self.bot.application_info()).description,
            )
            view = BaseView(ctx)
            view.add_item(CogSelect(ctx))
            message = await ctx.send(embed=embed, view=view)
            view.message = message

        elif command is None:  # Send cog help
            cog = cog.capitalize()

            _cog: commands.Cog = self.bot.get_cog(cog)
            if _cog is None:
                raise MissingCog(f"Cannot find cog: {cog}")
            if cog in CONSTANTS.Cogs().FORBIDDEN_COGS:
                raise ForbiddenData("Sorry! No help command is available for that.")
            cog: commands.Cog = _cog

            view = CommandView(ctx, cog)
            embed = await view.page_zero(ctx.interaction)

            sel = CogSelect(ctx)
            sel.placeholder = "%s Cog Selection..." % cog.ge()
            sel.options.remove(discord.utils.get(sel.options, label=cog.qualified_name))
            view.add_item(sel)
            await view.checkButtons()

            message = await ctx.send(embed=embed, view=view)
            view.message = message

        elif cog is None:  # Send command help
            _command: Optional[
                Union[commands.HybridCommand, commands.Command]
            ] = self.bot.get_command(command)
            if _command is None:
                raise MissingCommand(f"Cannot find command: {command}")
            command: commands.HybridCommand = _command

            view = BaseView(ctx)
            view.add_item(CogSelect(ctx))

            embed = await self.command_embed(ctx, command)
            message = await ctx.send(embed=embed, view=view)
            view.message = message
        else:
            _cog: commands.Cog = self.bot.get_cog(cog)
            if _cog is None:
                raise MissingCog(f"Cannot find cog: {cog}")
            cog: commands.Cog = _cog

            _command: Optional[
                Union[commands.HybridCommand, commands.Command]
            ] = utils.get(explode(cog.get_commands()), qualified_name=command.lower())
            print([x.qualified_name for x in explode(cog.get_commands())])
            if _command is None:
                raise MissingCommand(
                    f"Cannot find command: {command} in cog: {cog.qualified_name}"
                )
            command: commands.HybridCommand = _command

            view = BaseView(ctx)
            view.add_item(CogSelect(ctx))

            embed = await self.command_embed(ctx, command)
            message = await ctx.send(embed=embed, view=view)
            view.message = message

    @help.autocomplete("cog")
    async def cog_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return sorted(
            [
                discord.app_commands.Choice(name=c, value=c)
                for c in list(self.bot.cogs.keys())
                if ((current.lower() in c.lower() or (c.lower()) in current.lower()))
                and c not in CONSTANTS.Cogs().FORBIDDEN_COGS
            ][:25],
            key=lambda c: c.name,
        )

    @help.autocomplete("command")
    async def command_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return sorted(
            [
                discord.app_commands.Choice(
                    name="[{}] {}".format(c.cog_name, c.qualified_name),
                    value=c.qualified_name,
                )
                for c in (
                    explode([c for c in self.bot.commands])
                    if not getattr(inter.namespace, "cog")
                    else explode(
                        self.bot.get_cog(inter.namespace.cog).get_commands()
                        if (self.bot.get_cog(inter.namespace.cog)) is not None
                        or inter.namespace.cog in CONSTANTS.Cogs().FORBIDDEN_COGS
                        else []
                    )
                    if inter.namespace.cog in [c for c, _ in self.bot.cogs.items()]
                    else []
                )
                if (
                    (current.lower() in c.qualified_name.lower())
                    or (c.qualified_name.lower() in current.lower())
                )
                and c.cog_name not in CONSTANTS.Cogs().FORBIDDEN_COGS
            ][:25],
            key=lambda c: c.name[c.name.index("]") + 1 :],
        )

    async def main_embed(self, ctx: commands.Context, bot: commands.Bot):
        return fmte(
            ctx,
            t="Help",
            d="Hello there! {}\n**Cogs:** `{}`\n**Commands:** `{}`".format(
                (await self.bot.application_info()).description,
                len(self.bot.cogs),
                len(explode(self.bot.commands)),
            ),
        )

    async def command_embed(
        self, ctx: commands.Context, command: commands.HybridCommand
    ):
        async def getDef(param: CommandParameter):
            try:
                return str(await param.get_default(ctx))
            except TypeError:
                return "None"

        def simplifyAnnotation(param: commands.Parameter):
            anno: Any = param.annotation

            # Unwrap Optionals
            if isinstance(anno, typing._UnionGenericAlias):
                anno = anno.__args__[0]

            if hasattr(
                anno, "max_value"
            ):  # Because python be fucky and discord be shady
                return f"{str(anno.type().name).capitalize()} Range [Minimum: {anno.min_value()}, Maximum: {anno.max_value()}]"
            return anno.__name__

        class FakeParam:
            def __init__(self) -> None:
                self.description = "No Description. Please use /bug and tell me..."

        async def formatParams(embed: discord.Embed):
            params = list(command.clean_params.items())
            for n, v in [
                (
                    f"**`{name}`:**",
                    f"""
                    ㅤㅤ**Description:** `{command.app_command._params.get(param.name, FakeParam()).description}`
                    ㅤㅤ**Type:** `{simplifyAnnotation(param)}`
                    ㅤㅤ**Default:** `{await getDef(param)}`
                    ㅤㅤ**Reqiuired:** `{str(param.required)}`""",
                )
                for name, param in params
            ]:
                embed.add_field(name=n, value=v, inline=False)
            return embed

        as_strings: List[str] = [x.qualified_name for x in command.parents]
        as_strings.sort(key=str.__len__)

        parents = ", ".join(as_strings) or None
        embed = fmte(
            ctx,
            t=f"`{command.qualified_name}`\nCog: `{command.cog_name}`\nGroup[s]: `{parents}`",
            d=f"`/{command.qualified_name} {command.signature}`\n*{command.short_doc}*",
        )
        if command.params:
            embed.add_field(
                name="***Parameters:***", value="-----------------------------------"
            )
            embed = await formatParams(embed)
        return embed


class CommandView(Paginator):
    def __init__(
        self,
        ctx: commands.Context,
        cog: commands.Cog,
    ):
        values: List[commands.HybridCommand] = sorted(
            explode(cog.get_commands()), key=lambda c: c.qualified_name
        )

        super().__init__(ctx, values, 5, timeout=45)

    async def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter, t="Commands: Page `{}` of `{}`".format(self.position, self.maxpos)
        )

    async def adjust(self, embed: discord.Embed):
        start = self.pagesize * (self.position - 1)
        stop = self.pagesize * (self.position)

        for command in self.vals[start:stop]:
            command: commands.HybridCommand = command
            embed.add_field(
                name=f"`/{command.qualified_name}`",
                value=f"*{command.short_doc}*",
                inline=False,
            )
        return embed


class CogSelect(discord.ui.Select):  # Shows all cogs in the bot
    def __init__(self, ctx: commands.Context):
        placeholder = "\N{MEDIUM WHITE CIRCLE} Cog Selection..."
        options = []

        self.ctx = ctx
        self.lastrem = None

        for name, cog in ctx.bot.cogs.items():
            if name in CONSTANTS.Cogs().FORBIDDEN_COGS:
                continue
            options.append(
                discord.SelectOption(
                    label=name, description=cog.description, emoji=cog.ge()
                )
            )
        super().__init__(
            placeholder=placeholder,
            options=options,
        )

    async def callback(self, interaction: Interaction) -> Any:
        opt = interaction.data["values"][0]
        obj = self.ctx.bot.get_cog(opt)
        self.placeholder = f"{obj.ge()} Cog Selection..."
        if self.lastrem:
            self.append_option(self.lastrem)
        self.lastrem = utils.get(self.options, label=obj.qualified_name)
        self.options.remove(self.lastrem)
        self.options = sorted(self.options, key=lambda o: o.label)

        view = CommandView(self.ctx, obj)
        embed = await view.page_zero(interaction)
        await view.checkButtons()
        view.add_item(self)

        await interaction.response.edit_message(embed=embed, view=view)
        view.message = await interaction.original_message()


async def setup(bot):
    await bot.add_cog(Help(bot))
