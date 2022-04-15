import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

import os
import asyncio

from dotenv import load_dotenv
from _aux.extensions import load_extensions
from cogs.Help import Help

load_dotenv()

intents = discord.Intents.all()
activity = discord.Activity(type = discord.ActivityType.listening, name = ">>help")



bot: commands.Bot = commands.Bot(
    command_prefix = when_mentioned_or(">>",),
    case_insensitive = True,
    intents = intents,
    activity = activity,
    application_id="963411905018466314",
    help_command = Help()
)


async def main():
    await load_extensions(bot, False, True)
    await bot.start(os.getenv("BOT_KEY"))

asyncio.run(main())


