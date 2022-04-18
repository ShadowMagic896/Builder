from _aux.constants import Constants
from _aux.embeds import fmte
from discord.ext import commands
from typing import List, Dict, Any, Optional

class Help(commands.HelpCommand, commands.Cog):
    async def send_bot_help(self, mapping: Dict[Any | None, List[Any]]):
        ctx = self.context
        embed = fmte(
            self.context, 
            t = "Help Screen",
            d = """Prefix: `<mention> or >>`
            My commands are grouped into `Groups`
            To call a group command, use `>><group> <command> <options>`
            To see info on a `Group` (seen below), use `>>help <Group>`
            To see info on a `Command`, use `>>help <group> <command>`
            """
        )
        gps: List[commands.HybridGroup] = ctx.bot.commands
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
            t = "**Command Group `{}`**".format(group.name),
            d = "**All Commands:**\n{}".format("".join(["ㅤㅤ`>>{} {} {}`\nㅤㅤ*{}*\n\n".format(
                group.name, 
                c.name, 
                c.signature, 
                c.short_doc
            ) for c in group.commands]))
        )
        await ctx.send(embed = embed)
    
    async def send_command_help(self, command: commands.Command, /) -> None:
        ctx = self.context
        embed = fmte(
            ctx,
            t = "{} [Cog: `{}` Group: `{}`]".format(command.name, command.cog.qualified_name, command.parent),
            d = "```>>{}{} {}```".format("{} ".format(command.parent.name) if command.parent else "", command.name, command.signature)
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help())
