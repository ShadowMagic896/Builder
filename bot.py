from socket import gaierror, socket
from urllib.parse import quote_plus
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

import asyncio
from dotenv import load_dotenv
import pymongo
from pymongo.server_api import ServerApi
import logging
import os

from botAuxiliary.Extensions import load_extensions

load_dotenv()

# Logging ---------------------------------------------------
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='data\\logs\\_discord.log',
    encoding='utf-8',
    mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# -----------------------------------------------------------


class Builder(commands.Bot):
    def __init__(self):
        command_prefix = when_mentioned_or("dev>>")
        intents = discord.Intents.default()
        intents.members = True
        activity = discord.Activity(
            type=discord.ActivityType.listening, name="/help")
        help_command = None
        self.session: aiohttp.ClientSession = None
        self.tab_balances = None
        super().__init__(
            command_prefix=command_prefix,
            case_insensitive=True,
            intents=intents,
            activity=activity,
            application_id="963411905018466314",
            help_command=help_command
        )

    async def setup_hook(self) -> None:
        print(f"Client online [User: {self.user}, ID: {self.user.id}]")
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        databasename = "values"
        host = f"mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@cluster0.sywtj.mongodb.net/{quote_plus(databasename)}?retryWrites=true&w=majority"
        server_api = ServerApi('1')

        self.client = pymongo.MongoClient(host=host, server_api=server_api)
        self.database = self.client["database"]
        self.collections = {"balances": self.database["balances"], "items": self.database["items"]}


async def main():
    bot = Builder()
    await bot.load_extension("jishaku")
    log = await load_extensions(bot, ["./src/cogs", "./src/economy",], spaces = 20)
    print(log)
    await bot.start(os.getenv("BOT_KEY"))
asyncio.run(main())
