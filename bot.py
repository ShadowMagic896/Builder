from codecs import ignore_errors
from typing import List, Union
from urllib.parse import quote_plus
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import when_mentioned_or

import asyncio
import pymongo
from pymongo.server_api import ServerApi
import logging
import os

from src.auxiliary.bot.Extensions import load_extensions
from src.auxiliary.bot.Stats import Stats
from data.config import Config

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
        command_prefix: List[str] = when_mentioned_or("dev>>")
        help_command: Union[commands.HelpCommand, None] = None
        tree_cls: type = discord.app_commands.CommandTree
        intents: discord.Intents = discord.Intents.default()
        intents.members = True
        
        activity: discord.Activity = discord.Activity(type=discord.ActivityType.watching, name=f"{Stats.lineCount(['.'])} LINES")
        application_id: str = "963411905018466314"
        case_insensitive: bool = True
        
        super().__init__(
            command_prefix=command_prefix,
            help_command=help_command,
            tree_cls=tree_cls,
            intents=intents,

            activity=activity,
            application_id=application_id,
            case_insensitive=case_insensitive,
        )
        status: str = "idle"
        self.status = discord.Status(status)

        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

        username = quote_plus(Config().DB_USERNAME)
        password = quote_plus(Config().DB_PASSWORD)
        databasename = quote_plus("values")
        host = f"mongodb+srv://{username}:{password}@cluster0.sywtj.mongodb.net/{databasename}?retryWrites=true&w=majority"
        server_api = ServerApi("1")

        self.client = pymongo.MongoClient(host=host, server_api=server_api)
        self.database = self.client["database"]

        # This exists purely to protect me from typos. If I misspell a collection, instead of creating a new one, I will just get a key error.
        self.collections = {"balances": self.database["balances"], "items": self.database["items"]}

    async def setup_hook(self) -> None:
        spaces = len("                         ")
        client = str(self.user) + " " * (spaces - len(str(self.user)))
        ID = str(self.user.id) + " " * (spaces - len(str(self.user.id)))
        version = discord.__version__ + " " * (spaces - len(str(discord.__version__)))
        s = """
              \N{WHITE HEAVY CHECK MARK} ONLINE 
+-----------------------------------+
| Client: %s |
+-----------------------------------+
| ID Num: %s |
+-----------------------------------+
| Version: %s|
+-----------------------------------+
        """ % (client, ID, version)
        print(s)

async def main():
    bot = Builder()
    await bot.load_extension("jishaku")
    log = await load_extensions(bot, ["./src/cogs/development", "./src/cogs/economy", "./src/cogs/main"], spaces = 20, ignore_errors = False)
    print(log)
    await bot.start(Config().BOT_KEY)
asyncio.run(main())