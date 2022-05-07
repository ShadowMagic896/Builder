import math
import discord
from discord.app_commands import describe
from discord.ext import commands

import random
from typing import List, Mapping, Optional

from _aux.sql3OOP import Table
from _aux.embeds import fmte, fmte_i


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
    @commands.cooldown(2, 15, commands.BucketType.user)
    @describe(
        user = "The user to get the balance of"
    )
    async def balance(self, ctx: commands.Context, user: Optional[discord.Member]):
        """
        Returns your current balance.
        """
        user = user or ctx.author
        if user.bot:
            raise TypeError("User cannot be a bot.")
        data = self.getUserBal(user, 0)

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
        if user.bot:
            raise TypeError("User cannot be a bot.")
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
        if user.bot:
            raise TypeError("User cannot be a bot.")
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
        amount = random.randint(max(-500, -self.getUserBal(ctx.author)), 1000)
        if amount < 0:
            k = random.choice([
                "Some villain saw you begging and mugged you. Sucks to suck.", 
                "You tripped on the curb and somehow lost your wallet. Nice job...",
                "You ate the coins. For some reason."
            ])
        elif amount > 0:
            k = random.choice([
                "You saw someone begging and decied to mug them. You villain!", 
                "Some buffoon left some coins out on the road, might as well keep them for good fortune.",
                "You found some coins in the toilet... why were you looking there!?"
            ])
        else:
            k = "You did nothing, and nothing happened."
        self.addToBal(ctx.author, amount)
        embed = fmte(
            ctx,
            t = "{}{} Sheckels".format("+" if amount >= 0 else "", amount),
            d = k
        )
        await ctx.send(embed=embed)
    
    @cur.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def leaderboard(self, ctx: commands.Context):
        """
        See who's the wealthiest in this server
        """
        data = self.tab.select(values=["userid", "balance"])
        values: Mapping[discord.Member, int] = {ctx.guild.get_member(userid): balance for userid, balance in data if userid in [member.id for member in ctx.guild.members]}
        inst = LeaderboardView(self.bot, False, values, 5)
        embed = inst.page_zero(ctx.interaction)
        view = inst
        view.checkButtons()
        await ctx.send(embed=embed, view=view)
    
    @commands.command()
    @commands.is_owner()
    async def manualadd(self, ctx: commands.Context, user: Optional[discord.Member], amount: Optional[int] = 1000):
        self.addToBal(user or ctx.author, amount)
    
    @commands.command()
    @commands.is_owner()
    async def manualset(self, ctx: commands.Context, user: Optional[discord.Member], amount: Optional[int]):
        self.setBal(user or ctx.author, amount)

    @commands.command()
    @commands.is_owner()
    async def manualdel(self, ctx: commands.Context, user: Optional[discord.Member]):
        self.tab.delete(conditions=["userid=%s" % (user or ctx.author).id])
    
    def clamp(self, value: int, lower_bound: int = None, upper_bound: int = None):
        return max(min(value, upper_bound or value), lower_bound or value)
    

    
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

class LeaderboardView(discord.ui.View):
    def __init__(self, bot: commands.Bot, ephemeral: bool, values: Mapping[discord.Member, int],
                 pagesize: int, *, timeout: Optional[float] = 180, ):
        self.bot = bot
        self.ephemeral = ephemeral
        self.vals = sorted(list(values.items()), key = lambda v: v[1], reverse=True)
        self.pos = 1
        self.maxpos = math.ceil((len(self.vals) / pagesize))
        self.pagesize = pagesize

        super().__init__(timeout=timeout)

    @discord.ui.button(emoji="<:BBArrow:971590922611601408> ", custom_id="bb")
    async def fullback(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos = 1
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:BArrow:971590903837913129>", custom_id="b")
    async def back(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos -= 1
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.red, custom_id="x")
    async def close(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.message.delete()

    @discord.ui.button(emoji="<:FArrow:971591003893006377>", custom_id="f")
    async def next(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos += 1
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:FFArrow:971591109874704455>", custom_id="ff")
    async def fullnext(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos = self.maxpos
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)
        
    def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter,
            t="Leaderboard: Page `{}` of `{}`".format(self.pos, self.maxpos)
        )

    def add_fields(self, embed: discord.Embed):
        for c, t in enumerate(self.vals[self.pagesize *
                                 (self.pos - 1):self.pagesize * (self.pos)]):
            user, bal = t[0], t[1]
            embed.add_field(
                name="{}: {}".format((c+1) + (self.pos-1) * self.pagesize, user),
                value="`%s`" % Currency(self.bot).formatBalance(bal),
                inline=False
            )
        return embed

    def page_zero(self, interaction: discord.Interaction):
        self.pos = 1
        return self.add_fields(self.embed(interaction))

    def checkButtons(self, button: discord.Button = None):
        if self.maxpos == 1:
            for b in self.children:
                if isinstance(b, discord.ui.Button) and b.custom_id != "x":
                    b.disabled = True
                    b.style = discord.ButtonStyle.grey
        else:
            if self.pos == 1:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("b", "bb"):
                            b.disabled = True
            else:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("b", "bb"):
                            b.disabled = False
            if self.pos == self.maxpos:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("f", "ff"):
                            b.disabled = True
            else:
                for b in self.children:
                    if isinstance(b, discord.ui.Button):
                        if b.custom_id in ("f", "ff"):
                            b.disabled = False
        if button is None:
            return
        for b in [c for c in self.children if isinstance(
                c, discord.ui.Button) and c.custom_id != "x"]:
            if b == button:
                b.style = discord.ButtonStyle.success
            else:
                b.style = discord.ButtonStyle.secondary
                
    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True



async def setup(bot):
    await bot.add_cog(Currency(bot))
