import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

import os
import asyncio
import logging

from dotenv import load_dotenv
from _aux.extensions import load_extensions
from Help import Help

load_dotenv()

# Logging ---------------------------------------------------
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='_discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# -----------------------------------------------------------



intents = discord.Intents.all()
activity = discord.Activity(type = discord.ActivityType.listening, name = ">>help")



bot: commands.Bot = commands.Bot(
    command_prefix = when_mentioned_or(">>", "<@!963411905018466314>", ),
    case_insensitive = True,
    intents = intents,
    activity = activity,
    application_id="963411905018466314",
    help_command = Help()
)

async def main():
    # await bot.load_extension("jishaku")
    await load_extensions(bot, False, True)
    await bot.start(os.getenv("BOT_KEY"))

asyncio.run(main())


