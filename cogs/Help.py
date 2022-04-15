from _aux.constants import Constants
from _aux.embeds import fmte
from discord.ext import commands
from typing import Mapping, Optional, List, Dict, Any

class Help(commands.HelpCommand, commands.Cog):
    async def send_bot_help(self, mapping: Dict[Any | None, List[Any]]):
        embed = fmte(
            ctx = self.context, 
            t = "Help Screen",
            d = "Prefix: `<mention> or >>`\nCommands: `{}`".format(len(self.context.bot.commands))
        )

        for cog, cmds in mapping.items():
            if str(cog) in Constants.ExtensionConstants.FORBIDDEN_COGS: continue
            embed.add_field(
                name = "***{}***".format(cog.qualified_name),       # get the cog name
                value = f"{len(cmds)} commands",  # get a count of the commands in the cog.
                inline = False
            )
        await self.context.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Help())
