
import discord
from discord.ext import commands
from _aux.constants import Constants
from _aux.embeds import fmte
from typing import List, Dict, Any, Optional

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
            t = "**Command Group `{}`**".format(
                group.name
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
            t = "{} [Cog: `{}` Group: `{}`]".format(command.name, cogname, command.parent),
            d = "```>>{}{} {}```".format("{} ".format(command.parent.name) if command.parent else "", command.name, command.signature)
        )
        await ctx.send(embed=embed)
    
    async def send_cog_help(self, cog: commands.Cog, /) -> None:
        if cog.qualified_name.lower() in [c.name for c in self.context.bot.commands]:
            grp = self.context.bot.get_command(cog.qualified_name.lower())
            await self.send_group_help(grp)
        else:
            raise commands.errors.CommandNotFound("I could not find that group")