import discord
from discord.ext import commands
from discord.ext.commands.errors import *
from discord.errors import *

import asyncio
import sqlite3
import os
import time
from datetime import datetime
import pytz

from _aux.embeds import fmte
from _aux.sql3OOP import Table


class Watchers(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Client online [User: {self.bot.user}, ID: {self.bot.user.id}]")
        # await self.prep_channels()

    async def prep_channels(self):
        channel: discord.TextChannel = ...
        for guild in self.bot.guilds:
            for chan in guild.channels:
                if "log" in chan.name.lower():
                    channel = chan
                    break
            else:
                channel = await guild.create_text_channel(
                    name="Mod-Log",
                    reason="Automatic mod-log channel creation",
                    category=guild.categories[0],  # Uppermost category,
                    position=len(
                        guild.categories[0].text_channels) - 1  # Last spot
                )
            embed = discord.Embed(
                title="Mod Log Channel Made / Found",
                description="All logging will be sent here.",
                color=discord.Color.teal()
            )
            embed.timestamp = datetime.utcnow()
            await channel.send(embed=embed)
            tab = Table("data/guild_settings", "mod_channels",
                        {"guildid": "int", "channelid": "int"})
            if tab.select(values=["channelid"], conditions=[
                          f"guildid={guild.id}"]).fetchone():
                tab.update(values=[str(guild.id), str(channel.id)], conditions=[
                           f"guildid={str(guild.id)}"])
            else:
                tab.insert([guild.id, channel.id])
        tab.finish()

    async def prep_guild_channels(self, guild: discord.Guild):
        for chan in guild.channels:
            if "log" in chan.name.lower():
                channel = chan
                break
        else:
            channel = await guild.create_text_channel(
                name="Mod Log",
                reason="Automatic mod-log channel creation",
                category=guild.categories[0],  # Uppermost category,
                position=len(
                    guild.categories[0].text_channels) - 1  # Last spot
            )
        embed = discord.Embed(
            title="Mod Log Channel Made / Found",
            description="All logging will be sent here.",
            color=discord.Color.teal()
        )
        embed.timestamp = datetime.utcnow()
        await channel.send(embed=embed)
        tab = Table("data/guild_settings", "mod_channels",
                    {"guildid": "int", "channelid": "int"})
        if tab.select(values=["channelid"], conditions=[
                      f"guildid={guild.id}"]).fetchone():
            tab.update(values=[str(guild.id), str(channel.id)],
                       conditions=[f"guildid={str(guild.id)}"])
        else:
            tab.insert([guild.id, channel.id])
        tab.finish()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # await self.prep_guild_channels(guild)
        pass

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        mes = "Auth: {}; Com: {} [{}]; T: {}; Parents: {}; Children: {};\n".format(
            ctx.author,
            ctx.command.qualified_name,
            ctx.command_failed,
            datetime.now(tz=pytz.timezone("UTC")),
            ctx.invoked_parents,
            ctx.invoked_subcommand,
        )
        open("_commandlog.txt", "ab").write(mes.encode("UTF-8"))

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        hint = None

        if "jishaku" in ctx.invoked_parents:  # Do not automate command errors for this cog
            return

        if isinstance(
                error, commands.CommandInvokeError):  # Unwrap CommandInvokeErrors
            error = error.original

        if isinstance(error, CommandNotFound):
            hint = "I couldn't find that command. Try `/help`"
        if isinstance(error, ExtensionNotFound):
            hint = "I couldn't find that cog. Try `/help`"
        elif isinstance(error, NotFound):
            hint = "I couldn't find that. Try `/help`, or check the error for more info."
        elif isinstance(error, Forbidden):
            hint = "I'm not allowed to do that."
        elif isinstance(error, MissingRequiredArgument):
            hint = "You need to supply more information to use that command. Try `/help [command]`"
        elif isinstance(error, NSFWChannelRequired):
            hint = "You must be in an NSFW channel to use that."
        elif isinstance(error, UserNotFound):
            hint = "That user was not found in discord."
        elif isinstance(error, MemberNotFound):
            hint = "That user was not found in this server."
        elif isinstance(error, BadArgument):
            hint = "You passed an invalid option."
        elif isinstance(error, asyncio.TimeoutError):
            hint = "This has timed out. Next time, try to be quicker."
        else:
            hint = "I'm not sure what went wrong, probably an internal error. Please contact `Cookie?#9461` with information on how to replicate the error you just recieved."
        embed = fmte(
            ctx,
            t="An Error Occurred.",
            d="**Hint:**\n{}\n**Error:**\n`{}`".format(
                hint,
                error
            ),
            c=discord.Color.red()
        )
        await ctx.send(embed=embed, ephemeral=True)
        ctx.command_failed = True

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        if "jishaku" in ctx.invoked_parents or "jsk" in ctx.invoked_parents:
            return

        if ctx.command_failed:
            await ctx.message.add_reaction("‼️")
        else:
            await ctx.message.add_reaction("☑️")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild and message.author is not self.bot.user:
            data = "{} at {}: {}\n".format(
                message.author, datetime.fromtimestamp(
                    time.time()), message.content)
            open("_dmlog.txt", "a").write(data)
        # await self.bot.process_commands(message) # This is no longer
        # necessary in 2.0.0?


async def setup(bot):
    await bot.add_cog(Watchers(bot))
