import discord
from discord.ext import commands

import asyncio
import os

from _aux.extensions import load_extensions
from _aux.embeds import fmte

class Dev(commands.Cog):
    """
    This cog is for any commands that help users find information about other users, this bot, the server, etc.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
    
    @commands.hybrid_group(aliases = ["devs", "developers", "team", "owners"])
    async def dev(self, ctx):
        app = (await self.bot.application_info())
        embed = fmte(
            ctx,
            t = "Hello! I'm {}.".format(self.bot.user.display_name),
            d = "Devs on **{}**:\n{}".format(app.team.name, "\n".join(["**{}#{}**".format(member.name, member.discriminator) for member in app.team.members]))
        )
        embed.set_image(url=app.team.icon)

        await ctx.send(embed=embed)
        
    @dev.command()
    @commands.is_owner()
    async def load(self, ctx, cog: str = "*", logging: bool = True):
        log = ""
        if cog == "*":
            for cog in os.listdir("./cogs"):
                
                if cog.endswith(".py") and not cog.startswith("_"):
                    try:
                        await self.bot.load_extension(f"cogs.{cog[:-3]}")
                        log += f"✅ {cog}\n"
                            
                    except commands.errors.ExtensionAlreadyLoaded:
                        await self.bot.reload_extension(f"cogs.{cog[:-3]}")
                        log += f"✅ {cog}\n"

                    except Exception as err:
                        print(err)
                        log += f"❌ {cog} [{err}]\n"
        if logging: await ctx.send(log, ephemeral = True)
    
    
    @dev.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[int], spec: str = None) -> None:
        """
        [Owner only] Syncs all commands.
        Usage: >>sync [guilds_ids*] [spec: str]
        """
        if not guilds:
            if spec == "*":
                fmt = await ctx.bot.tree.sync(guild=ctx.guild)
            else:
                fmt = await ctx.bot.tree.sync()

            await ctx.send(
                "Synced {} commands {}".format(len(fmt), "globally" if not spec else "to the current guild.")
            )
            return

        fmt = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                fmt += 1
        await load_extensions(logging=True)
        await ctx.send(f"Synced the tree to {fmt}/{len(guilds)} guilds.")
    
    @dev.command()
    async def get_log(self, ctx: commands.Context):
        file: discord.File = discord.File("_commandlog.txt", "commandlog.txt")
        embed: discord.Embed = fmte(
            ctx,
            t = "Log fetched."
        )
        await ctx.send(embed = embed, file = file)
    
    @dev.command()
    @commands.is_owner()
    async def rectest(self, ctx: commands.Context):
        pass

    @dev.command()
    @commands.is_owner()
    async def kill(self, ctx: commands.Context):
        embed = fmte(
            ctx,
            t = "Bot Shutting Down..."
        )
        await ctx.send(embed = embed)
        await self.bot.close()

    @dev.command()
    @commands.is_owner()
    async def clearcache(self, ctx: commands.Context):
        self.bot.clear()
        embed = fmte(
            ctx,
            "Cache cleared."
        )
        await ctx.send(embed = embed)

        
async def setup(bot):
    await bot.add_cog(Dev(bot))