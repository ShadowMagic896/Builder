from code import interact
import sqlite3
from typing import List
import discord
from discord import Interaction, app_commands
from discord.ext import commands

import asyncio
import os

from _aux.extensions import load_extensions
from _aux.embeds import fmte, fmte_i
from _aux.userio import is_user

class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
    
    def ge(self):
        return "👨🏻‍💻"
        
    # @app_commands.command()
    # @commands.is_owner()
    # async def load(self, ctx, cog: str = "*", logging: bool = True):
    #     """
    #     Loads the bot's cogs
    #     """
    #     log = ""
    #     if cog == "*":
    #         for cog in os.listdir("./cogs"):
                
    #             if cog.endswith(".py") and not cog.startswith("_"):
    #                 try:
    #                     await self.bot.load_extension(f"cogs.{cog[:-3]}")
    #                     log += f"✅ {cog}\n"
                            
    #                 except commands.errors.ExtensionAlreadyLoaded:
    #                     await self.bot.reload_extension(f"cogs.{cog[:-3]}")
    #                     log += f"✅ {cog}\n"

    #                 except Exception as err:
    #                     print(err)
    #                     log += f"❌ {cog} [{err}]\n"
    #     if logging: await ctx.send(log, ephemeral = True)
    
    

    
    # @app_commands.command()
    # @commands.is_owner()
    # async def get_log(self, inter: Interaction):
    #     """
    #     Returns the bot's commandlog
    #     """
    #     file: discord.File = discord.File("_commandlog.txt", "commandlog.txt")
    #     embed: discord.Embed = fmte_i(
    #         inter,
    #         t = "Log fetched."
    #     )
    #     await inter.response.send_message(embed = embed, file = file, ephemeral=True)

    # @app_commands.command()
    # @commands.is_owner()
    # async def kill(self, ctx: commands.Context):
    #     """
    #     Turns off the bot.
    #     """
    #     embed = fmte(
    #         ctx,
    #         t = "Bot Shutting Down..."
    #     )
    #     await ctx.send(embed = embed)
    #     await self.bot.close()

    # @app_commands.command()
    # @commands.is_owner()
    # async def ccache(self, inter: Interaction):
    #     """
    #     Clears the bot's cache
    #     """
    #     self.bot.clear()
    #     embed = fmte_i(
    #         inter,
    #         "Cache cleared."
    #     )
    #     await inter.response.send_message(embed = embed, ephemeral=True)
    
    # @app_commands.command()
    # @commands.is_owner()
    # async def cmds(self, inter: Interaction):
    #     """
    #     Returns a list of all of the bot's commands
    #     """
    #     data = ""
    #     for c in self.bot.commands:
    #         if hasattr(c, "commands"): # It's a group
    #             data += "\nGroup: {}\nㅤㅤ{}".format(
    #                 c.qualified_name,
    #                 "\nㅤㅤ".join(["{} {}".format(c.name, c.aliases) for c in c.commands])
    #             )
    #         else: # Just a command
    #             data += "\nCommand: {}".format(
    #                 c.qualified_name
    #             )
    #     await inter.response.send_message("```{}```".format(data), ephemeral=True)
    
    # @app_commands.command()
    # @commands.is_owner()
    # async def dms(self, ctx: commands.Context, user: str):
    #     """
    #     Gets all dms from a user
    #     """
    #     channel = await self.bot.create_dm(is_user(ctx, user))
    #     async for m in channel.history(limit = 200):
    #         attachments: List[discord.Attachment] = m.attachments
    #         await ctx.send("T: {}\nAttachments: {}\nID: {}".format(m.content, "\nㅤㅤ".join([a.url for a in attachments]), m.id),)
    
    # @app_commands.command()
    # @commands.is_owner()
    # async def sigs(self, ctx: commands.Context):
    #     """
    #     Gets signatures of all commands
    #     """
    #     data = ""
    #     for c in self.bot.commands:
    #         if hasattr(c, "commands"): # It's a group
    #             for r in c.commands:
    #                 data += "{}: {}\n".format(r.qualified_name, r.signature)
    #         else:
    #             data += "{} {}\n".format(c.qualified_name, c.signature)
    #     await ctx.send("```{}```".format(data))

    # @app_commands.command()
    # @commands.is_owner()
    # async def dm(self, ctx: commands.Context, user: str):
    #     """
    #     Dms a user
    #     """
    #     embed = fmte(
    #         ctx,
    #         t = "Please send the message to be sent to the user."
    #     )
    #     await ctx.send(embed = embed)
    #     ms: discord.Message = await self.bot.wait_for("message", check = lambda m: m.author == ctx.author)
    #     user: discord.User = await is_user(ctx, user)
    #     if not user:
    #         embed = fmte(
    #             ctx,
    #             t = "Cannot find that user."
    #         )
    #         await ctx.send(embed = embed)
    #         return
    #     urls = "\n".join([c.url for c in ms.attachments])
    #     await user.send(
    #         content = "{}\n{}".format(ms.content, urls),
    #         embeds = ms.embeds,
    #     )

        
async def setup(bot):
    await bot.add_cog(Dev(bot))