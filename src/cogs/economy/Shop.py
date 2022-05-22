import time
from typing import List, Optional, Union
import asyncpg
import hashlib
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
    
    @commands.hybrid_group()
    async def shop(self, ctx: commands.Context):
        pass

    @shop.command()
    async def view(self, ctx: commands.Context):
        
        pass

class ShopDatabase:
    def __init__(self, ctx: commands.Context) -> None:
        self.ctx: commands.Context = ctx
        self.apg: asyncpg.Connection = ctx.bot.apg
    
    async def getAll(self, users: Optional[List[Union[discord.User, discord.Member]]]) -> List[asyncpg.Record]:
        command = """
            SELECT * FROM shops
            WHERE userid IN $1
        """
        allEntries: List[asyncpg.Record] = await self.apg.fetch(command, str([user.id for user in users]))
        return allEntries
    
    async def delete(self, transactionID: str) -> str:
        command = """
            DELETE FROM shops
            WHERE transactionid = $1::TEXT
        """
        result: str = await self.apg.execute(command, transactionID)
        return result

    async def createShop(self, user: Union[discord.Member, discord.User], atomid: int, amount: int, price: int, endunix: int) -> asyncpg.Record:
        """
        Creates a shop entry. Returns the transaction's record.
        """
        command = """
            INSERT INTO shops(userid, atomid, amount, price, startunix, endunix)
            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5,
                $6
            )
            RETRURNING *
            ON CONFLICT(userid, atomid) DO UPDATE
            SET amount = $4, price = $5, startunix = $6, endunix = $7;
        """
        startunix = time.time()
        await self.apg.fetch(command, user.id, atomid, amount, price, startunix, endunix)