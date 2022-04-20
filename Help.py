
from array import array
import discord
from discord.ext import commands
from discord.ext.commands.help import _HelpCommandImpl
from _aux.constants import Constants
from _aux.embeds import fmte
from typing import List, Dict, Any, Optional
from cogs.Watchers import Watchers

class Help(commands.HelpCommand):
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