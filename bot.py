import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

import os
import asyncio
import logging

from dotenv import load_dotenv
from _aux.extensions import load_extensions
from Help.TextHelp import EmbedHelp
from cogs.InterHelp import InterHelp    

load_dotenv()

# Logging ---------------------------------------------------
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='_discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# -----------------------------------------------------------


class Builder(commands.AutoShardedBot):
    def __init__(self):
        command_prefix = when_mentioned_or(">>")
        intents = discord.Intents.all()
        activity = discord.Activity(type = discord.ActivityType.listening, name = "/help")
        help_command = None


        super().__init__(
            command_prefix = command_prefix,
            case_insensitive = True,
            intents = intents,
            activity = activity,
            application_id="963411905018466314",
            help_command = help_command
        )

async def main():
    bot = Builder()
    await bot.load_extension("jishaku")
    await load_extensions(bot, False, True)
    await bot.start(os.getenv("BOT_KEY"))

asyncio.run(main())


