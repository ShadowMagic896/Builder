
from array import array
from tkinter.tix import Select
import discord
from discord import AppInfo, Embed, SelectOption
from discord.ext import commands
from discord.ext.commands.help import _HelpCommandImpl
from _aux.constants import Constants
from _aux.embeds import fmte
from typing import List, Dict, Any, Mapping, Optional
from cogs.Watchers import Watchers


class EmbedHelp(commands.HelpCommand):
    def get_options(self) -> List[discord.SelectOption]:
        """
        Returns a list of discord.SelectOptions that represent all of the user-available cogs as well as their emojis.
        """
        options: List[discord.SelectOption] = []

        for name, cog in self.context.bot.cogs.items():
            if name in ["Dev", "GUI", "Watchers", "Jishaku"]:
                continue
            options.append(
                SelectOption(
                    label=name,
                    description=cog.description,
                    emoji=cog.ge())
            )
        return options

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]], /) -> None:
        ctx: commands.Context = self.context

        options: List[discord.SelectOption] = self.get_options()

        application: AppInfo = await ctx.bot.application_info()

        embed: discord.Embed = fmte(
            ctx,
            t="**Hello! I'm {}.**".format(
                ctx.bot.user.display_name,
            ),
            d="**Prefix:**\n`>> or <mention>`\n\n**Who I am:**\n{}\n\n**My Team:**\nㅤㅤ{}".format(
                application.description,
                "ㅤㅤ\n".join([str(u) for u in application.team.members])
            )
        )

        view: discord.ui.View = BaseHelpView(ctx)
        view.add_item(
            HelpSelect(
                ctx,
                placeholder="Please choose an option...",
                options=options))

        await ctx.send(embed=embed, view=view)

    async def send_cog_help(self, cog: commands.Cog, /) -> None:

        ctx: commands.Context = self.context

        embed: discord.Embed = fmte(
            ctx,
            t="Cog: `{}`\nCommands: {}".format(
                cog.qualified_name,
                len(cog.get_commands())
            ),
            d=cog.description
        )
        for c in cog.get_commands():
            embed.add_field(
                name="[{}] `{} {}`".format(
                    "Cmd" if isinstance(c, commands.HybridCommand) else "Grp",
                    c.name,
                    c.signature
                ),
                value="*{}*\n`>>help {}`".format(
                    c.short_doc,
                    c.name
                ),
                inline=False
            )

        options: List[discord.SelectOption] = self.get_options()

        view: discord.ui.View = BaseHelpView(self.context)
        view.add_item(
            HelpSelect(
                self.context,
                placeholder="Please choose an option...",
                options=options))

        await ctx.send(embed=embed, view=view)

    async def _send_cog_help(self, ctx: commands.Context, cog: commands.Cog, /) -> None:

        embed: discord.Embed = fmte(
            ctx,
            t="Cog: `{}`\nCommands: `{}`".format(
                cog.qualified_name,
                len(cog.get_commands())
            ),
            d=cog.description
        )
        for c in cog.get_commands():
            embed.add_field(
                name="[{}] `{} {}`".format(
                    "CMD" if isinstance(c, commands.HybridCommand) else "GRP",
                    c.qualified_name,
                    c.signature
                ),
                value="*{}*\n`>>help {}`".format(
                    c.short_doc,
                    c.name
                ),
                inline=False
            )

        return embed

    async def send_group_help(self, group: commands.Group[Any, ..., Any], /) -> None:
        ctx = self.context

        embed = fmte(
            ctx,
            t="`{}` [Cog: `{}`]\nCommands: `{}`".format(
                group.name, group.cog_name, len(group.commands)),
        )
        for c in group.commands:
            embed.add_field(
                name="`{} {}`".format(
                    c.qualified_name,
                    c.signature
                ),
                value="*{}*\n`>>help {}`".format(
                    c.short_doc,
                    c.name
                ),
                inline=False
            )

        view = BaseHelpView(ctx)
        view.add_item(
            HelpSelect(
                ctx,
                "Please choose an option..."),
            self.get_options())
        await ctx.send(embed=embed, view=view)

    async def send_command_help(self, command: commands.Command[Any, ..., Any], /) -> None:
        ctx = self.context
        embed = fmte(
            ctx,
            t="`{}` [Cog: `{}`, Grp: `{}`]\nAliases: `{}`".format(
                command.name, command.cog_name, command.parent, command.aliases),
            d="*{}*\n`>>{} {}`".format(
                command.short_doc,
                command.qualified_name,
                command.signature
            )
        )
        view = BaseHelpView(ctx)
        view.add_item(
            HelpSelect(
                ctx,
                placeholder="Please choose an option...",
                options=self.get_options()))
        await ctx.send(embed=embed, view=view)

    async def send_error_message(self, error: str, /) -> None:
        attempt = error.split()[3][1:-1]
        for cogname, cog in self.context.bot.cogs.items():
            if cogname.lower() == attempt.lower():
                await self.send_cog_help(cog)
                return
        else:
            for com in self.context.bot.commands:
                if com.name.lower() == attempt.lower():
                    if isinstance(com, commands.HybridCommand):
                        await self.send_command_help(com)
                        return
                    elif isinstance(com, commands.HybridGroup):
                        await self.send_group_help(com)
                        return
                    else:
                        raise commands.CommandError(
                            "Something happened: Command not Command or Group")
            else:
                raise commands.errors.CommandNotFound(error)

    # async def on_help_command_error(self, ctx: commands.Context, error: commands.CommandError, /) -> None:
    #     attempt = ctx.command
    #     for cog in ctx.bot.cogs:
    #         if cog.name.lower() == attempt.lower():
    #             await self.send_cog_help(cog)
    #             return
    #     else:
    #         raise commands.errors.CommandNotFound("Cannot find that Cog")


class BaseHelpView(discord.ui.View):
    """
    This is meant to be used with `.add_item()` and `HelpSelect`
    """

    def __init__(self, ctx: commands.Context, timeout=30):
        super().__init__(timeout=timeout)
        self.ctx: commands.Context = ctx


class HelpSelect(discord.ui.Select):
    """
    This is meant to be added as an item to `BaseHelpView`
    """

    def __init__(self, ctx: commands.Context, *, placeholder, options) -> None:
        super().__init__(placeholder=placeholder, options=options)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction) -> Any:
        if self.ctx.author != interaction.user:
            return

        selected = interaction.data["values"][0]
        cog = self.ctx.bot.get_cog(selected)

        try:
            await interaction.response.send_message()
        except BaseException:
            pass
        embed = await EmbedHelp()._send_cog_help(self.ctx, cog)
        await interaction.message.edit(embed=embed)
