from _aux.constants import Constants
from _aux.embeds import fmte
from discord.ext import commands
from typing import Mapping, Optional, List, Dict, Any

class Help(commands.HelpCommand, commands.Cog):
    async def send_bot_help(self, mapping: Dict[Any | None, List[Any]]):
        embed = fmte(
            self.context, 
            t = "Help Screen",
            d = "Prefix: `<mention> or >>`\nCommands: `{}`".format(len(self.context.bot.commands))
        )

        for cog, cmds in mapping.items():
            if not cog or str(cog.qualified_name) in Constants.ExtensionConstants.FORBIDDEN_COGS: continue
            embed.add_field(
                name = "***{}***".format(cog.qualified_name),
                value = "{} group{}".format(len(cmds), "s" if len(cmds) != 1 else ""),
                inline = False
            )
        await self.context.send(embed = embed)
    
    async def send_cog_help(self, cog: commands.Cog, /) -> None:
        ctx = self.context
        embed = fmte(
            ctx,
            t = "All Commands / Command Groups in {}".format(cog.qualified_name),
            d = ""
        )
        for c in cog.get_commands():
            embed.add_field(
                name = "{}: `{}` {}".format("Group" if hasattr(c, "commands") else "Command", c.name, " {}".format(c.aliases) if c.aliases else ""),
                value = "```>>{}{} {}```".format("help " if hasattr(c, "commands") else "", c.name, c.signature),
                inline = False
            )
        await ctx.send(embed = embed)
    
    async def send_group_help(self, group: commands.Group, /) -> None:
        ctx = self.context
        embed = fmte(
            ctx,
            t = group.qualified_name,
            d = ""
        )
        for c in group.commands:
            embed.add_field(
                name = "Command: `{}{}`".format(c.name, " {}".format(c.aliases) if c.aliases else ""),
                value = "```>>{} {} {}```".format(c.parent, c.name, c.signature),
                inline = False
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
