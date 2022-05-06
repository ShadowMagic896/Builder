import math
import discord
from discord.app_commands import describe
from discord.ext import commands

import random
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
    @commands.cooldown(2, 30, commands.BucketType.user)
    @describe(
        user = "The user to get the balance of"
    )
    async def balance(self, ctx: commands.Context, user: Optional[discord.Member]):
        """
        Returns your current balance.
        """
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
    @commands.cooldown(2, 30, commands.BucketType.user)
    @describe(
        user = "The user to give money to",
        amount = "How much money to give"
    )
    async def give(self, ctx: commands.Context, user: discord.Member, amount: int):
        """
        Sends money to a user.
        """
        if amount < 1:
            raise ValueError("You can't give a negative amount, silly!")
        if (cv := self.getUserBal(ctx.author)) < amount:
            raise ValueError("You don't have that much money!")
        embed = fmte(
            ctx,
            t = "Are You Sure You Want to Give `%s` Sheckels to `%s`?" % (amount, user),
            d = f"This is `{round((amount / cv) * 100, 2)}%` of your money."
        )
        await ctx.send(embed=embed, view=GiveView(self.bot, ctx, amount, ctx.author, user))
    
    @cur.command()
    @commands.cooldown(2, 120, commands.BucketType.user)
    @describe(
        user = "The user to request money from",
        amount = "How much money to request"
    )
    async def request(self, ctx: commands.Context, user: discord.Member, amount: int):
        """
        Requests money from a user.
        """
        perms = ctx.channel.permissions_for(user)
        if not (perms.read_message_history or perms.read_messages):
            raise TypeError("That user cannot see this channel.")
        if amount < 1:
            raise ValueError("You can't ask for a negative amount, silly!")
        if (cv := self.getUserBal(user)) < amount:
            raise ValueError("They don't have that much money!")
        embed = fmte(
            ctx,
            t = "`{}`, Do You Want to Give `{}` `{}` Sheckels?".format(user, ctx.author, amount),
            d = f"This is `{round((amount / cv) * 100, 2)}%` of your money."
        )
        await ctx.send(user.mention, embed=embed, view=RequestView(self.bot, ctx, amount, ctx.author, user))
    
    @cur.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def beg(self, ctx: commands.Context):
        """
        Begs for money. You can win some, but you can also lose some.
        """
        amount = random.randint(-500, 1000)
        if amount < 0:
            k = random.choice([
                "Some villan saw you begging and mugged you. Sucks to suck.", 
                "You tripped on the curb and somehow lost your wallet. Nice job...",
                "You ate the coins. For some reason."
            ])
        elif amount > 0:
            k = random.choice([
                "You saw someone begging and decied to mug them. You villan!.", 
                "Some buffoon left some coins out on the road, might as well keep them for good fortune.",
                "You found some coins in the toilet... why were you looking there!?"
            ])
        else:
            k = "You did nothing, and nothing happened."
            
        amount = self.clamp(amount, lower_bound = self.getUserBal(ctx.author))
        self.addToBal(ctx.author, -amount)
        embed = fmte(
            ctx,
            t = "{}{} Sheckels".format("+" if amount >= 0 else "", amount),
            d = k
        )
        await ctx.send(embed=embed)
    
    def clamp(self, value: int, lower_bound: int = None, upper_bound: int = None):
        return max(min(value, (upper_bound if upper_bound is not None else value)), (lower_bound if lower_bound is not None else value))
    

    
    async def cine(self, user: discord.Member, newbal: int = 0):
        if not self.tab.select(conditions="userid=%s" % user.id):
            self.tab.insert(values=[self.user.id, newbal])
            self.tab.commit()

    def formatBalance(self, bal: int):
        return "".join(["%s," % char if c %3 == 0 else char for c, char in enumerate(str(bal)[::-1])][::-1]).strip(",")

    def getUserBal(self, user: discord.User, default: int = 0) -> int:
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
        """
        Sets the user's current balance
        """
        self.cine(user)
        self.tab.update(values = ["balance=%s" % str(amount)], conditions = ["userid = %s" % user.id])
        self.tab.commit()

    def addToBal(self, user: discord.Member, amount: int) -> int:
        """
        Adds an amount of currency to a user's balance
        ## Returns
        The user's new balance
        """
        v = self.getUserBal(user)
        self.tab.update(values = ["balance=%s" % str(v + amount)], conditions = ["userid = %s" % user.id])
        self.tab.commit()
        return v + amount

class GiveView(discord.ui.View):
    def __init__(self, bot, ctx, amount, auth, user):
        self.bot: commands.AutoShardedBot = bot
        self.ctx: commands.Context = ctx
        self.amount: int = amount
        self.auth: discord.Member = auth
        self.user: discord.Member = user
        super().__init__()
    
    @discord.ui.button(label="Accept", emoji="✅", style=discord.ButtonStyle.primary)
    async def ack(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.auth:
            await inter.response.send_message("This is not your interaction.")
            return
        inst = Currency(self.bot)
        authnew = inst.addToBal(self.auth, -self.amount)
        usernew = inst.addToBal(self.user, self.amount)
        embed = fmte(
            self.ctx,
            t = "Transaction Completed",
            d = "`{}` balance: `{}`\n`{}` balance: `{}`".format(
                self.auth, authnew,
                self.user, usernew
            )
        )
        await inter.response.edit_message(content=None, embed=embed, view=None)
    
    @discord.ui.button(label="Decline", emoji="❌", style=discord.ButtonStyle.danger)
    async def dec(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.auth:
            await inter.response.send_message("This is not your interaction.")
            return
        embed = fmte(
            self.ctx,
            t = "Transaction Declined",
            d = "No currency has been transfered."
        )
        for c in self.children:
            c.disabled = True
        await inter.response.edit_message(content=None, embed=embed, view=None)
                    
    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True

class RequestView(discord.ui.View):
    def __init__(self, bot, ctx, amount, auth, user):
        self.bot: commands.AutoShardedBot = bot
        self.ctx: commands.Context = ctx
        self.amount: int = amount
        self.auth: discord.Member = auth
        self.user: discord.Member = user
        super().__init__()
    
    @discord.ui.button(label="Accept", emoji="✅", style=discord.ButtonStyle.primary)
    async def ack(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.user:
            await inter.response.send_message("This is not your interaction.")
            return
        inst = Currency(self.bot)
        authnew = inst.addToBal(self.auth, self.amount)
        usernew = inst.addToBal(self.user, -self.amount)
        embed = fmte(
            self.ctx,
            t = "Transaction Completed",
            d = "`{}` balance: `{}`\n`{}` balance: `{}`".format(
                self.auth, authnew,
                self.user, usernew
            )
        )
        await inter.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Decline", emoji="❌", style=discord.ButtonStyle.danger)
    async def dec(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.user:
            await inter.response.send_message("This is not your interaction.")
            return
        embed = fmte(
            self.ctx,
            t = "Transaction Declined",
            d = "No currency has been transfered."
        )
        for c in self.children:
            c.disabled = True
        await inter.response.edit_message(embed=embed, view=None)
                
    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True



async def setup(bot):
    await bot.add_cog(Currency(bot))
