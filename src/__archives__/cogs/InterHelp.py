import discord
from discord import app_commands, Interaction
from discord.app_commands import describe
from discord.ext import commands

import os

from typing import Any, List, Optional
from src.auxiliary.bot.Constants import CONSTANTS


from src.auxiliary.user.Embeds import fmte, fmte_i, Desc


class InterHelp(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_command()
    @describe(
        cog="The cog to show help on.",
        command="The command to show help on.",
        ephemeral=Desc.ephemeral,
    )
    async def help(self, ctx: commands.Context, cog: str = None, command: str = None, ephemeral: bool = False):
        """
        Get a guide on what I can do.
        """
        if not cog and not command:
            embed = await self.main_embed(ctx, self.bot)

            view = self.get_view(
                self.bot, ctx, ephemeral,
            )
            await ctx.send(embed=embed, view=view, ephemeral=ephemeral)
            return

        if cog and not command:
            cogs = [v for c, v in self.bot.cogs.items() if c.lower()
                    == cog.lower()]

            if not cogs:
                raise commands.errors.BadArgument(cog)

            embed = InterHelp(self.bot)._cog_embed_ctx(ctx, cogs[0])
            view = self.get_view(
                self.bot, ctx, ephemeral,
                cog=cogs[0]
            )
            await ctx.send(embed=embed, view=view, ephemeral=ephemeral)

        elif command and not cog:
            cmds = [
                c for c in self.explode(
                    self.bot.commands) if c.qualified_name.lower() == command.lower()]

            if not cmds:
                raise commands.errors.BadArgument(command)

            embed = InterHelp(
                self.bot)._command_embed(
                ctx.interaction,
                cmds[0])

            view = self.get_view(
                self.bot, ctx, ephemeral,
                cog=cmds[0].cog,
            )
            await ctx.send(embed=embed, view=view, ephemeral=ephemeral)

        elif command and cog:
            _cog: commands.Cog = self.bot.get_cog(cog)
            if not _cog:
                raise commands.errors.BadArgument(cog)
            cog: commands.Cog = _cog

            _command: commands.HybridCommand = [r for r in self.explode(
                cog.get_commands()) if r.qualified_name.lower() == command.lower()]

            if not _command:
                raise commands.errors.BadArgument(command)
            command: commands.HybridCommand = _command[0]

            embed = self._command_embed_ctx(ctx, command)

            view = self.get_view(
                self.bot, ctx, ephemeral,
                cog=cog
            )

            await ctx.send(embed=embed, view=view, ephemeral=ephemeral)

    # hahah code in one line go brrrrr
    def explode(self, l: List[commands.HybridCommand]):
        """
        A recursive func to flatten all commands into one list
        """
        l = list(l)
        nl = []
        for c in l:
            if isinstance(c, (commands.HybridGroup, commands.Group)):
                nl.extend(self.explode(c.commands))
            else:
                nl.append(c)
        return nl

    @help.autocomplete("cog")
    async def cog_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        return sorted([discord.app_commands.Choice(name=c, value=c) for c in list(self.bot.cogs.keys())if ((current.lower() in c.lower(
        ) or (c.lower()) in current.lower())) and c not in CONSTANTS.Cogs().FORBIDDEN_COGS][:25], key=lambda c: c.name)

    @help.autocomplete("command")
    async def command_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        return sorted(
            [
                discord.app_commands.Choice(
                    name="[{}] {}".format(
                        c.cog_name, c.qualified_name), value=c.qualified_name) for c in (
                    self.explode([c for c in self.bot.commands]) if not getattr(
                        inter.namespace, "cog") else self.explode(self.bot.get_cog(
                            inter.namespace.cog).get_commands()) if inter.namespace.cog in [
                                c for c, v in self.bot.cogs.items()] else []) if (
                                    (current.lower() in c.qualified_name.lower()) or (
                                        c.qualified_name.lower() in current.lower())) and c.cog_name not in CONSTANTS.Cogs().FORBIDDEN_COGS][
                                            :25], key=lambda c: c.name[
                                                c.name.index("]") + 1:])

    def raisecog(self, cog: str):
        for c, v in self.bot.cogs.items():
            if c.lower() == cog.lower():
                return v
        else:
            raise commands.errors.ExtensionNotFound(cog)

    def raisegroup(self, group: str):
        for n, g in [
            (g.name, g) for g in self.bot.commands if isinstance(
                g, app_commands.Group)]:
            if group.lower() == n.lower():
                return g
        else:
            raise commands.errors.ExtensionNotFound(group)

    def raisecommand(self, command: str):
        e = commands.errors.ExtensionNotFound(
            command) if command not in self.explode(self.bot.commands) else None
        if e:
            raise e

        for c in self.explode(self.bot.commands):
            if c.name.lower() == command:
                return c
        else:
            raise commands.errors.ExtensionNotFound(command)

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

    def _cog_embed(self, inter, cog: commands.Cog):
        return fmte_i(
            inter,
            t="Cog: `{}`".format(cog.qualified_name),
            d="**Commands:** {}\n*{}*".format(
                len(self.explode(cog.get_commands())), cog.description)
        )

    def _group_embed(self, inter, group: commands.HybridGroup):
        return fmte_i(
            inter,
            t="Group: `{}`".format(group.qualified_name),
            d="**Commands:** {}\n*{}*".format(len(group.commands),
                                              group.description)
        )

    def _command_embed(
            self,
            inter,
            command: commands.HybridCommand,
            color=discord.Color.teal()):
        return fmte_i(
            inter,
            t="`{}` [Cog: `{}`, Group: `{}`]".format(
                command.qualified_name,
                command.cog_name,
                command.parent
            ),
            d="```{} {}```\n*{}*".format(
                command.qualified_name, command.signature,
                command.short_doc
            ),
            c=color
        )

    def _cog_embed_ctx(self, ctx: commands.Context, cog: commands.Cog):
        return fmte(
            ctx,
            t="Cog: `{}`".format(cog.qualified_name),
            d="**Commands:** {}\n*{}*".format(
                len(cog.get_commands()), cog.description)
        )

    def _command_embed_ctx(
            self,
            ctx,
            command: commands.HybridCommand,
            color=discord.Color.teal()):
        return fmte(
            ctx,
            t="`{}` [Cog: `{}`, Group: `{}`]".format(
                command.qualified_name,
                command.cog_name,
                command.parent
            ),
            d="```{} {}```\n*{}*".format(
                command.qualified_name, command.signature,
                command.short_doc
            ),
            c=color
        )

    def _invite_embed(self, inter):
        return fmte_i(
            inter,
            t="Invite Me to a Server!",
            d="[Invite Link]({})".format(
                discord.utils.oauth_url(
                    self.bot.application_id,
                    permissions=discord.Permissions(8),
                    scopes=["bot", "applications.commands"],
                )
            )
        )

    def _os_embed(self, inter):
        return fmte_i(
            inter,
            t="I'm 100% Open Source!",
            d="View on [GitHub](%s)" %
            "https://github.com/ShadowMagic896/Builder")

    def get_view(
            self,
            bot: commands.Bot,
            context: commands.Context,
            ephemeral: bool,
            cog: commands.Cog = None):
        view = HelpMenu().add_item(CogSelect(bot, context, ephemeral))
        if cog:
            view.add_item(CommandSelect(bot, context, ephemeral, cog))

        view.add_item(MainMenu(bot, context, ephemeral))
        view.add_item(InviteLink(bot, context, ephemeral))
        view.add_item(OpenSrc(bot, context, ephemeral))
        if not ephemeral:
            view.add_item(CloseButton())

        return view


class HelpMenu(discord.ui.View):  # Base to add things on
    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)


class CogSelect(discord.ui.Select):  # Shows all cogs in the bot
    def __init__(self, bot: commands.Bot,
                 context: commands.Context, ephemeral: bool):
        placeholder = "Cog Selection..."
        options = []

        self.bot = bot
        self.context = context
        self.ephemeral = ephemeral

        for name, cog in bot.cogs.items():
            if name in CONSTANTS.Cogs().FORBIDDEN_COGS:
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

        embed = InterHelp(self.bot)._cog_embed(interaction, obj)
        view = InterHelp(
            self.bot).get_view(
            self.bot,
            self.context,
            self.ephemeral,
            cog=obj)

        await interaction.response.edit_message(embed=embed, view=view)


class CommandSelect(
        discord.ui.Select):  # Shows all commands from a certain cog
    def __init__(self, bot: commands.Bot, context: commands.Context,
                 ephemeral: bool, cog: commands.Cog,):
        placeholder = "Command Selection..."
        options = []

        self.bot = bot
        self.context = context
        self.ephemeral = ephemeral
        cmds = cog.get_commands()
        for c in cmds:
            if isinstance(c, commands.HybridGroup):
                cmds.extend(c.commands)
                cmds.remove(c)

        for command in cmds:
            options.append(
                discord.SelectOption(
                    label=command.qualified_name,
                    description=command.short_doc
                )
            )

        super().__init__(
            placeholder=placeholder,
            options=options,
        )

    async def callback(self, interaction: Interaction) -> Any:
        command: commands.HybridCommand = self.bot.get_command(
            interaction.data["values"][0])
        embed = InterHelp(self.bot)._command_embed(interaction, command)
        view = InterHelp(
            self.bot).get_view(
            self.bot,
            self.context,
            self.ephemeral,
            cog=command.cog)
        await interaction.response.edit_message(embed=embed, view=view)


class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close", emoji="❌", style=discord.ButtonStyle.red)
        self.message: discord.Message = ...

    async def callback(self, interaction: Interaction) -> Any:
        await interaction.message.delete()


class MainMenu(discord.ui.Button):
    def __init__(self, bot, context, ephemeral):
        self.bot = bot
        self.context = context
        self.ephemeral = ephemeral
        super().__init__(label="Menu", emoji="📃", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: Interaction) -> Any:
        embed = await InterHelp(self.bot).main_embed(self.context, self.bot)
        view = InterHelp(
            self.bot).get_view(
            self.bot,
            self.context,
            self.ephemeral)
        await interaction.response.edit_message(embed=embed, view=view)


class InviteLink(discord.ui.Button):
    def __init__(self, bot, context, ephemeral):
        self.bot = bot
        self.context = context
        self.ephemeral = ephemeral
        super().__init__(label="Invite", emoji="📨", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: Interaction) -> Any:
        embed = InterHelp(self.bot)._invite_embed(interaction)
        view = InterHelp(self.bot).get_view(
            self.bot, self.context, self.ephemeral)
        await interaction.response.edit_message(embed=embed, view=view)


class OpenSrc(discord.ui.Button):
    def __init__(
            self,
            bot: commands.Bot,
            context: commands.Context,
            ephemeral: bool):
        self.bot = bot
        self.context = context
        self.ephemeral = ephemeral
        super().__init__(label="View OS", emoji="👨🏻‍💻", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: Interaction) -> Any:
        embed = InterHelp(self.bot)._os_embed(interaction)
        view = InterHelp(self.bot).get_view(
            self.bot, self.context, self.ephemeral)
        await interaction.response.edit_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(InterHelp(bot))