from client_container import *

class Help(commands.HelpCommand, commands.Cog):
    async def send_bot_help(self, mapping):
        channel = self.get_destination()
        user = None
        async for m in channel.history(limit=3):
            if m and m.author != None and not m.author.bot:
                user = m.author
                break
        

        embed = fmte(t="Help!", u = user)

        for cog, cmds in mapping.items():
            if cog in Constants.ExtensionConstants.FORBIDDEN_COGS: continue
            else: pass
            print("{} not in {}".format(cog, Constants.ExtensionConstants.FORBIDDEN_COGS))
            embed.add_field(
                name = "***{}***".format(cog.qualified_name if cog else "Unnamed"),       # get the cog name
                value = f"{len(cmds)} commands"  # get a count of the commands in the cog.
            )
            
        await channel.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Help())