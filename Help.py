
from array import array
from tkinter.tix import Select
import discord
from discord import Embed, SelectOption
from discord.ext import commands
from discord.ext.commands.help import _HelpCommandImpl
from _aux.constants import Constants
from _aux.embeds import fmte
from typing import List, Dict, Any, Mapping, Optional
from cogs.Watchers import Watchers

class TextHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        ctx: commands.Context = self.context
        embed = fmte(
            ctx, 
            t = "Help Screen",
            d = """Prefix: `<mention> or >>`
            My commands are grouped into `Groups`
            To call a group command, use `>><group> <command> <options>`
            To see info on a `Group` (seen below), use `>>help <Group>`
            To see info on a `Command`, use `>>help <group> <command>`
            """
        )
        gps = ctx.bot.commands
        for group in gps:
            if group.name in Constants.ExtensionConstants.FORBIDDEN_GROUPS:
                continue
            embed.add_field(
                name = "**Group `{}`**".format(group.name),
                value = "Commands: {}".format(len(group.commands)),
                inline = False
            )
        await ctx.send(embed = embed)
    
    async def send_group_help(self, group: commands.Group, /) -> None:
        ctx = self.context
        embed = fmte(
            ctx,
            t = "**Command Group `{} [A.K.A.: {}]`**".format(
                group.name,
                group.aliases
            ),
            d = "**Description:**\n{}\n**All Commands:**\n{}".format(
                group.short_doc, 
                "".join(["ㅤㅤ`>>{} {} {}`\nㅤㅤ*{}*\n\n".format(
                    group.name, 
                    c.name, 
                    c.signature, 
                    c.short_doc
                ) for c in group.commands])
            )
        )
        await ctx.send(embed = embed)
    
    async def send_command_help(self, command: commands.Command, /) -> None:
        ctx = self.context
        if command.cog:
            cogname = command.cog.qualified_name
        else:
            cogname = None
        embed = fmte(
            ctx,
            t = "{} [Cog: `{}` Group: `{}`]\n`A.K.A: {}`".format(
                command.name, 
                cogname, 
                command.parent, 
                command.aliases
            ),
            d = "```>>{}{} {}```\n*{}*".format(
                "{} ".format(command.parent.name) if command.parent else "", 
                command.name, 
                command.signature, 
                command.short_doc
            )
        )
        await ctx.send(embed=embed)
    
    async def send_cog_help(self, cog: commands.Cog, /) -> None:
        if cog.qualified_name.lower() in [c.name for c in self.context.bot.commands]:
            grp = self.context.bot.get_command(cog.qualified_name.lower())
            await self.send_group_help(grp)
        else:
            raise commands.errors.CommandNotFound("I could not find that group")
    
    async def send_error_message(self, error: str, /) -> None:
        if error.startswith("No command called "):
            com = error.split()[3][1:-1]
            
            coms = [c.commands for c in self.context.bot.commands if not isinstance(c, _HelpCommandImpl) and hasattr(c, "commands")]
            _coms = []
            for c in coms:
                for r in c:
                    _coms.append(r)

            coms = _coms
            cmds: List[commands.HybridCommand] = [c for c in coms if c.name == com.lower() or c.name in [r.lower() for r in c.aliases]]
            if len(cmds) == 0:
                raise commands.errors.CommandNotFound(error)
            elif len(cmds) == 1:
                c: commands.HybridCommand = cmds[0]
                embed = fmte(
                    self.context,
                    t = "{} [Cog: `{}` Group: `{}`]\n`A.K.A: {}`".format(
                        c.name, 
                        c.cog_name, 
                        c.parent, 
                        c.aliases
                    ),
                    d = "`>>{} {} {}`".format(
                        c.parent,
                        c.name,
                        c.signature
                    )
                )
                await self.context.send(embed = embed)
                return
            else:
                embed = fmte(
                    self.context,
                    t = "Multiple commands found, please choose a specific one.",
                )
                for c in cmds:
                    embed.add_field(
                        name = "{} [Cog: `{}` Group: `{}`]\n`A.K.A: {}`".format(
                            c.name, 
                            c.cog_name if c.cog_name else "Utility", #idk 
                            c.parent, 
                            c.aliases
                        ),
                        value = "`>>{} {} {}`\n*{}*".format(
                            c.parent,
                            c.name,
                            c.signature,
                            c.short_doc
                        ),
                        inline = False
                    )
                await self.context.send(embed = embed)


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
                SelectOption(label = name, description = cog.description, emoji = cog.ge())
            )
        return options

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]], /) -> None:
        ctx: commands.Context = self.context

        options: List[discord.SelectOption] = self.get_options()

        embed: discord.Embed = fmte(
            ctx,
            t = "Help",
            d = "Hello! I'm {}.\nPrefix: `>> or <mention>`\nYou can use `>>help <cog>` to find more information on a cog.\nAll Cogs:".format(ctx.bot.user.display_name)
        )

        view: discord.ui.View = BaseHelpView(ctx)
        view.add_item(HelpSelect(ctx, placeholder = "Please choose an option...", options = options))

        await ctx.send(embed = embed, view = view)
    
    async def send_cog_help(self, cog: commands.Cog, /) -> None:
        
        ctx: commands.Context = self.context

        embed: discord.Embed = fmte(
            ctx,
            t = "Cog: `{}`\nCommands: {}".format(
                cog.qualified_name,
                len(cog.get_commands())
            ),
            d = cog.description
        )
        for c in cog.get_commands():
            embed.add_field(
                name = "[{}] `{} {}`".format(
                    "Cmd" if isinstance(c, commands.HybridCommand) else "Grp",
                    c.name,
                    c.signature
                ),
                value = "*{}*\n`>>help {}`".format(
                    c.short_doc,
                    c.name
                ),
                inline = False
            )

        options: List[discord.SelectOption] = self.get_options()

        view: discord.ui.View = BaseHelpView(self.context)
        view.add_item(HelpSelect(self.context, placeholder = "Please choose an option...", options = options))
        
        await ctx.send(embed = embed, view = view)
    
    async def _send_cog_help(self, ctx: commands.Context, cog: commands.Cog, /) -> None:

        embed: discord.Embed = fmte(
            ctx,
            t = "Cog: `{}`\nCommands: `{}`".format(
                cog.qualified_name,
                len(cog.get_commands())
            ),
            d = cog.description
        )
        for c in cog.get_commands():
            embed.add_field(
                name = "[{}] `{} {}`".format(
                    "CMD" if isinstance(c, commands.HybridCommand) else "GRP",
                    c.qualified_name,
                    c.signature
                ),
                value = "*{}*\n`>>help {}`".format(
                    c.short_doc,
                    c.name
                ),
                inline = False
            )

        return embed
    
    async def send_group_help(self, group: commands.Group[Any, ..., Any], /) -> None:
        ctx = self.context

        embed = fmte(
            ctx,
            t = "`{}` [Cog: `{}`]\nCommands: `{}`".format(group.name, group.cog_name, len(group.commands)),
        )
        for c in group.commands:
            embed.add_field(
                name = "`{} {}`".format(
                    c.qualified_name,
                    c.signature
                ),
                value = "*{}*\n`>>help {}`".format(
                    c.short_doc,
                    c.name
                ),
                inline = False
            )
        
        view = BaseHelpView(ctx)
        view.add_item(HelpSelect(ctx, "Please choose an option..."), self.get_options())
        await ctx.send(embed = embed, view = view)
    
    async def send_command_help(self, command: commands.Command[Any, ..., Any], /) -> None:
        ctx = self.context
        embed = fmte(
            ctx,
            t = "`{}` [Cog: `{}`, Grp: `{}`]\nAliases: `{}`".format(command.name, command.cog_name, command.parent, command.aliases),
            d = "*{}*\n`>>{} {}`".format(
                command.short_doc,
                command.qualified_name,
                command.signature
            )
        )
        view = BaseHelpView(ctx)
        view.add_item(HelpSelect(ctx, placeholder = "Please choose an option...", options = self.get_options()))
        await ctx.send(embed = embed, view = view)


class BaseHelpView(discord.ui.View):
    """
    This is meant to be used with `.add_item()` and `HelpSelect`
    """
    def __init__(self, ctx: commands.Context, timeout = 30):
        super().__init__(timeout = timeout)
        self.ctx: commands.Context = ctx
    
class HelpSelect(discord.ui.Select):
    """
    This is meant to be added as an item to `BaseHelpView`
    """
    def __init__(self, ctx: commands.Context, *, placeholder, options) -> None:
        super().__init__(placeholder = placeholder, options=options)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction) -> Any:
        if self.ctx.author != interaction.user:
            return
        
        selected = interaction.data["values"][0]
        cog = self.ctx.bot.get_cog(selected)

        try:
            await interaction.response.send_message()
        except:
            pass
        embed = await EmbedHelp()._send_cog_help(self.ctx, cog)
        await interaction.message.edit(embed = embed)
        




        