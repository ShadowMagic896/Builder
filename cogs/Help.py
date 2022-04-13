from ast import Dict
from more_itertools import last
from client_container import *

class Help(discord.ext.commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.command(name = "help", description = "Shows a help message with all of the bot's commands")
    async def help(self, ctx):
        commands: list(str) = [c for c in self.bot.commands if not c.cog_name in os.getenv("FORBIDDEN_COGS").split(";")]
        groups: dict = {}

        # Populate Groups
        for c, com in enumerate(commands):
            if (c == 0) or not (com.cog_name in list(groups.keys())):
                groups[com.cog_name] = [com,]
            else:
                groups[com.cog_name].append(com)



async def setup(bot):
    await bot.add_cog(Help(bot))