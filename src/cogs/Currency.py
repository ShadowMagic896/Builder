import discord
from discord.app_commands import describe
from discord.ext import commands

from typing import Optional

from _aux.sql3OOP import Table
from _aux.embeds import fmte


class Currency(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tab: Table = Table(
            "data/currency",
            "balances",
            values={
                "userid": "integer",
                "balance": "integer"})

    def ge(self):
        return "💰"

    @commands.hybrid_group()
    async def cur(self, ctx: commands.Context):
        pass

    @cur.command()
    async def bal(self, ctx: commands.Context, user: Optional[discord.Member]):
        user = user if user else ctx.author
        data = self.getUserBal(user)
        if data is None:
            self.tab.insert(values=[user.id, 0])
            data = self.getUserBal(user)

        embed = fmte(
            ctx,
            t="Balance: `%s`" % self.formatBalance(data)
        )
        await ctx.send(embed=embed)
    
    @cur.command()
    async def add(self, ctx: commands.Context, amount: int, user: Optional[discord.Member]):
        user = user if user else ctx.author
        self.addToBal(user, amount)
        data = self.getUserBal(user)

        embed = fmte(
            ctx,
            t="New Balance: `%s`" % self.formatBalance(data)
        )
        await ctx.send(embed=embed)

    def formatBalance(self, bal: int):
        return "".join(["%s," % char if c %
                       3 == 0 else char for c, char in enumerate(str(bal))]).strip(",")


    def getUserBal(self, user: discord.User, default: int = 0):
        d = self.tab.select(
            values=["balance"],
            conditions=[
                "userid == %s" %
                user.id]).fetchone()
            
        if d is not None:
            return d[0]
        else:
            self.tab.insert(values=[user.id, default])
            self.tab.commit()
            return self.getUserBal(user)

    def setBal(self, user: discord.Member, amount: int):
        self.tab.update(values = ["balance=%s" % str(amount)], conditions = ["userid = %s" % user.id])
        self.tab.commit()

    def addToBal(self, user: discord.Member, amount: int):
        v = self.getUserBal(user)
        self.tab.update(values = ["balance=%s" % str(v + amount)], conditions = ["userid = %s" % user.id])
        self.tab.commit()


async def setup(bot):
    await bot.add_cog(Currency(bot))
