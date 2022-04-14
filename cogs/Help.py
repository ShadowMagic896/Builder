from client_container import *

class Help(discord.ext.commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
    
    # @commands.hybrid_command(name = "help", description = "Shows a help message with all of the bot's commands")
    # async def help(self, ctx):
    #     commands: list(str) = [c for c in self.bot.commands if not c.cog_name in os.getenv("FORBIDDEN_COGS").split(";")]
    #     print(type(commands[0]))
    #     groups: dict = {}
    #     embed: discord.Embed = fmte(ctx, t = "Help message moment")

    #     # Populate Groups
    #     for c, com in enumerate(commands):
    #         if (c == 0) or not (com.cog_name in list(groups.keys())):
    #             groups[com.cog_name] = [com]
    #         else:
    #             groups[com.cog_name].append(com)
        
    #     for key, val in list(groups.items()):
    #         l = ""
    #         for c in val:
    #             c: discord.ext.commands.core.Command
                
    #         # embed.add_field(name = key, value = l, inline = False)
        
    #     await ctx.send(embed = embed)



async def setup(bot):
    await bot.add_cog(Help(bot))