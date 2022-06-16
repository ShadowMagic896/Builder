import typing
import discord
from discord import Interaction, utils
from discord.app_commands import describe
from discord.ext import commands

from typing import Any, List, Optional, Union
from data.settings import INVISIBLE_COGS
from src.utils.converters import Cog, Command, Group
from src.utils.user_io import (
    cog_autocomplete,
    group_autocomplete,
    command_autocomplete,
)

from src.utils.embeds import fmte, fmte_i
from src.utils.functions import explode
from src.utils.subclass import BaseView, Paginator
from bot import Builder, BuilderContext


class Help(commands.Cog):
    def __init__(self, bot: Builder):
        self.bot = bot

    @commands.hybrid_command()
    @describe(
        cog="The cog to view",
        group="The command group to view",
        command="The command to view",
    )
    async def help(
        self,
        ctx: BuilderContext,
        cog: Optional[Cog],
        group: Optional[Group],
        command: Optional[Command],
    ):
        """
        Creates a menu to navigate all of the bot's commands
        """
        if command:
            view = BaseView(ctx)
            view.add_item(CogSelect(ctx))

            embed = await self.command_embed(ctx, command)
            message = await ctx.send(embed=embed, view=view)
            view.message = message

        elif group:
            view = GroupView(ctx, group)
            embed = await view.page_zero(ctx.interaction)

            sel = CogSelect(ctx)
            if group.cog is not None:
                sel.placeholder = "%s Cog Selection..." % group.cog.ge()
                sel.options.remove(
                    discord.utils.get(sel.options, label=group.cog.qualified_name)
                )
                view.add_item(sel)
            await view.check_buttons()

            message = await ctx.send(embed=embed, view=view)
            view.message = message

        elif cog:

            view = CommandView(ctx, cog)
            embed = await view.page_zero(ctx.interaction)

            sel = CogSelect(ctx)
            sel.placeholder = "%s Cog Selection..." % cog.ge()
            sel.options.remove(discord.utils.get(sel.options, label=cog.qualified_name))
            view.add_item(sel)
            await view.check_buttons()

            message = await ctx.send(embed=embed, view=view)
            view.message = message

        else:
            embed = fmte(
                ctx,
                t="Help",
                d="*%s*" % (await self.bot.application_info()).description,
            )
            view = BaseView(ctx)
            view.add_item(CogSelect(ctx))
            message = await ctx.send(embed=embed, view=view)
            view.message = message

    @help.autocomplete("cog")
    async def cog_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return await cog_autocomplete(self.bot, inter, current)

    @help.autocomplete("group")
    async def group_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return await group_autocomplete(self.bot, inter, current)

    @help.autocomplete("command")
    async def command_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return await command_autocomplete(self.bot, inter, current)

    async def main_embed(self, ctx: BuilderContext, bot: commands.Bot):
        return fmte(
            ctx,
            t="Help",
            d="Hello there! {}\n**Cogs:** `{}`\n**Commands:** `{}`".format(
                (await self.bot.application_info()).description,
                len(self.bot.cogs),
                len(explode(self.bot.commands)),
            ),
        )

    async def command_embed(self, ctx: BuilderContext, command: commands.HybridCommand):
        async def getDef(param: commands.Parameter):
            if isinstance(param.displayed_default, Union[int, float, str]):
                return param.displayed_default
            try:
                return str(await param.get_default(ctx))
            except TypeError:
                return "None"

        def simplifyAnnotation(param: commands.Parameter):
            anno: Any = param.annotation

            # Unwrap Optionals
            if isinstance(anno, typing._UnionGenericAlias):
                anno = anno.__args__[0]
            if hasattr(anno, "__name__"):
                return anno.__name__
            else:
                if isinstance(
                    anno, discord.app_commands.transformers._TransformMetadata
                ):
                    return f"{str(anno.metadata.type().name).capitalize()} Range [Minimum: {anno.metadata.min_value()}, Maximum: {anno.metadata.max_value()}]"
                return anno.__class__.__name__

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
                    ㅤㅤ**Required:** `{str(param.required)}`""",
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
        ctx: BuilderContext,
        cog: commands.Cog,
    ):
        values: List[commands.HybridCommand] = sorted(
            explode(cog.get_commands()), key=lambda c: c.qualified_name
        )

        super().__init__(ctx, values, 5, timeout=45)

    async def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter, t=f"Commands: Page `{self.position+1}` of `{self.maxpos+1}`"
        )

    async def adjust(self, embed: discord.Embed):
        for command in self.value_range:
            command: commands.HybridCommand = command
            embed.add_field(
                name=f"`/{command.qualified_name}`",
                value=f"*{command.short_doc}*",
                inline=False,
            )
        return embed


class GroupView(Paginator):
    def __init__(self, ctx: BuilderContext, group: commands.HybridGroup):
        self.group = group
        values: List[commands.HybridCommand] = sorted(
            explode(group.commands), key=lambda c: c.qualified_name
        )
        super().__init__(ctx, values, 5, timeout=45)

    async def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter,
            t=f"`{self.group.name}`: Page `{self.position+1}` of `{self.maxpos+1}`",
        )

    async def adjust(self, embed: discord.Embed):
        for command in self.value_range:
            embed.add_field(
                name=f"/{command.qualified_name}",
                value=f"*{command.short_doc}*\n**Parameters:** {len(command.params)}",
                inline=False,
            )
        return embed


class CogSelect(discord.ui.Select):  # Shows all cogs in the bot
    def __init__(self, ctx: BuilderContext):
        placeholder = "\N{MEDIUM WHITE CIRCLE} Cog Selection..."
        options = []

        self.ctx = ctx
        self.lastrem = None

        for name, cog in ctx.bot.cogs.items():
            if name in INVISIBLE_COGS:
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
        await view.check_buttons()
        view.add_item(self)

        await interaction.response.edit_message(embed=embed, view=view)
        view.message = await interaction.original_message()


async def setup(bot):
    await bot.add_cog(Help(bot))
