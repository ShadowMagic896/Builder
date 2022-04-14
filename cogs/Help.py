from client_container import *

class Help(commands.HelpCommand, commands.Cog):
    async def send_bot_help(self, mapping):
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