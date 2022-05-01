import os
import discord


async def load_extensions(bot, ignore_errors=False, logging=True):
    """
    bot: Yout bot. Send when calling this command in your main
    ignore_errors: Whether to simply say that a cog has had an error and continue, or to stop all cog loading and give full traceback. Useful when degbugging
    logging: Whether to print the log of successes / failues after loading cogs. Will not print if ignore_errors is False and an error is encountered.
    """
    if ignore_errors:
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
    else:
        log = ""
        for cog in os.listdir("./src/cogs"):
            try:
                if cog.endswith(".py") and not cog.startswith("_"):
                    await bot.load_extension(f"cogs.{cog[:-3]}")
                    log += f"✅ {cog}\n" if logging else ""

            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                await bot.load_extension(f"cogs.{cog[:-3]}")
                log += f"✅ {cog} [Reloaded]\n" if logging else ""
        print(log)
