from email.mime import application
from socket import gaierror, socket
import time
from typing import List, Type, Union
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
from botAuxiliary.Stats import Stats

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
        command_prefix: List[str] = when_mentioned_or("dev>>")
        help_command: Union[commands.HelpCommand, None] = None
        tree_cls: type = discord.app_commands.CommandTree
        status: str = f"Online Since: <t:{round(time.time())}:R>"
        intents: discord.Intents = discord.Intents.default(); intents.members = True
        
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

        username = quote_plus(os.getenv("DB_USERNAME"))
        password = quote_plus(os.getenv("DB_PASSWORD"))
        databasename = quote_plus("values")
        host = f"mongodb+srv://{username}:{password}@cluster0.sywtj.mongodb.net/{databasename}?retryWrites=true&w=majority"
        server_api = ServerApi("1")

        self.client = pymongo.MongoClient(host=host, server_api=server_api)
        self.database = self.client["database"]

        # This exists purely to protect me from typos. If I misspell a collection, instead of creating a new one, I will just get a key error.
        self.collections = {"balances": self.database["balances"], "items": self.database["items"]}

    async def setup_hook(self) -> None:
        print(f"Client online [User: {self.user}, ID: {self.user.id}]")


async def main():
    bot = Builder()
    await bot.load_extension("jishaku")
    log = await load_extensions(bot, ["./src/cogs", "./src/economy", "./src/development"], spaces = 20)
    print(log)
    await bot.start(os.getenv("BOT_KEY"))
asyncio.run(main())
