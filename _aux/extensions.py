import os, discord

async def load_extensions(bot, logging = True):
        log = ""
        for cog in os.listdir("./cogs"):
            try:
                if cog.endswith(".py") and not cog.startswith("_"):
                    await bot.load_extension(f"cogs.{cog[:-3]}")
                    log += f"✅ {cog}\n" if logging else ""
                    
            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                await bot.load_extension(f"cogs.{cog[:-3]}")
                log += f"✅ {cog} [Reloaded]\n" if logging else ""

            except Exception as err:
                print(err)
                log += f"❌ {cog} [{err}]\n" if logging else ""
        print(log)


