from client_container import *

class OwnerManagement(commands.Cog):
    """
    This cog is for any commands that help users find information about other users, this bot, the server, etc.
    """

    def __init__(self, bot) -> None:
        self.bot = bot
    
    
    @commands.command()
    async def load(self, ctx, cog: str = "*", logging: bool = True):
        log = ""
        if cog == "*":
            for cog in os.listdir("./cogs"):
                
                if cog.endswith(".py") and not cog.startswith("_"):
                    try:
                        await self.bot.load_extension(f"cogs.{cog[:-3]}")
                        log += f"✅ {cog}\n"
                            
                    except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                        await self.bot.reload_extension(f"cogs.{cog[:-3]}")
                        log += f"✅ {cog}\n"

                    except Exception as err:
                        print(err)
                        log += f"❌ {cog} [{err}]\n"
        if logging: await ctx.send(log, ephemeral = True)

async def setup(bot):
    await bot.add_cog(OwnerManagement(bot))