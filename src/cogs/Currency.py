import math
import os
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

import random
from typing import Mapping, Optional

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
                "balance": "integer",})
        self.coin = "<:Coin:972565900110745630>"

    def ge(self):
        return "💰"

    @commands.hybrid_group()
    async def cur(self, ctx: commands.Context):
        pass

    @cur.command()
    @commands.cooldown(2, 15, commands.BucketType.user)
    @describe(
        user="The user to get the balance of"
    )
    async def balance(self, ctx: commands.Context, user: Optional[discord.User]):
        """
        Returns your current balance.
        """
        user = user or ctx.author
        if user.bot:
            raise TypeError("User cannot be a bot.")
        data = self.getUserBal(user, 0)

        embed = fmte(
            ctx,
            t="`%s`'s Balance: `%s`%s" % (user, self.formatBalance(data), self.coin)
        )
        await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(2, 30, commands.BucketType.user)
    @describe(
        user="The user to give money to",
        amount="How much money to give"
    )
    async def give(self, ctx: commands.Context, user: discord.User, amount: int):
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
            t="Are You Sure You Want to Give `%s`%s to `%s`?" % (amount, self.coin, user),
            d=f"This is `{round((amount / cv) * 100, 2)}%` of your money."
        )
        await ctx.send(embed=embed, view=GiveView(self.bot, ctx, amount, ctx.author, user))

    @cur.command()
    @commands.cooldown(2, 120, commands.BucketType.user)
    @describe(
        user="The user to request money from",
        amount="How much money to request"
    )
    async def request(self, ctx: commands.Context, user: discord.User, amount: int):
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
            t="`{}`, Do You Want to Give `{}` `{}`{}?".format(
                user,
                ctx.author,
                amount,
                self.coin),
            d=f"This is `{round((amount / cv) * 100, 2)}%` of your money.")
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
            t="`{}{}`{}".format("+" if amount >= 0 else "", amount, self.coin),
            d=k
        )
        await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def leaderboard(self, ctx: commands.Context):
        """
        See who's the wealthiest in this server
        """
        data = self.tab.select(values=["userid", "balance"])
        values: Mapping[discord.User,
                        int] = {ctx.guild.get_member(userid): balance for userid,
                                balance in data if userid in [member.id for member in ctx.guild.members]}
        view = LeaderboardView(self.bot, False, values, 5)
        embed = view.page_zero(ctx.interaction)
        view.checkButtons()
        await ctx.send(embed=embed, view=view)
    
    @cur.command()
    @commands.cooldown(3, 120, commands.BucketType.user)
    @describe(
        user = "The user to steal from",
        amount = "How to to attempt to steal"
    )
    async def steal(self, ctx: commands.Context, user: discord.User, amount: int):
        """
        Attempts to steal money from a user. You may gain some, but you may also lose some!
        """
        if user.bot:
            raise TypeError("Cannot steal from bots!")
        if user == ctx.author:
            raise ValueError("Cannot steal from yourself!")
        user_bal = self.getUserBal(user, 0)
        auth_bal = self.getUserBal(ctx.author, 0)
        if amount > auth_bal:
            raise ValueError("You cannot risk more than you own!")
        if amount > user_bal:
            raise ValueError("You cannot steal more than they own!")
        if amount < 1:
            raise ValueError("Invalid Amount")
        chnc = 0.60

        success = random.random() < chnc
        if success:
            na = self.addToBal(ctx.author, amount)
            nu = self.addToBal(user, -amount)
            embed = fmte(
                ctx,
                t = "Successful! You Stole `%s`%s." % (self.formatBalance(amount), self.coin),
                d = "**You Now Have:** `{}`{} [Before: `{}`{}]\n**{} Now Has:** `{}`{} [Before: `{}`{}]".format(
                    self.formatBalance(na), self.coin, self.formatBalance(auth_bal), self.coin, user.display_name, self.formatBalance(user_bal), self.coin, self.formatBalance(nu), self.coin
                ),
            )
            await ctx.send(embed=embed)
            embed = fmte(
                ctx,
                t = "`%s`%s Were Stolen From You!" % (self.formatBalance(amount), self.coin),
                d = "**Guild:** `{}`\n**User:** `{}`".format(
                    ctx.guild, ctx.author
                )
            )
            await user.send(embed=embed)
        else:
            na = self.addToBal(ctx.author, -amount)
            nu = self.addToBal(user, amount)
            embed = fmte(
                ctx,
                t = "Failure! You Gave Away `%s`%s" % (self.formatBalance(amount), self.coin),
                d = "**You Now Have:** `{}`{} [Before: `{}`{}]\n**{} Now Has:** `{}`{} [Before: `{}`{}]".format(
                    self.formatBalance(na), self.coin, self.formatBalance(auth_bal), self.coin, user.display_name, self.formatBalance(user_bal), self.coin, self.formatBalance(nu), self.coin
                ),
                c = discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @cur.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def hourly(self, ctx: commands.Context):
        """
        Claim your hourly Coins!
        """
        rate = int(os.getenv("HOURLY_CUR_RATE"))
        embed = fmte(
            ctx,
            t = "`%s`%s Gained!" % (self.formatBalance(rate), self.coin),
            d = "You now have: `%s`%s" % (self.formatBalance(self.addToBal(ctx.author, rate)), self.coin)
        )
        await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(1, 3600 * 24, commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        """
        Claim your daily Coins!
        """
        rate = int(os.getenv("DAILY_CUR_RATE"))
        embed = fmte(
            ctx,
            t = "`%s`%s Gained!" % (self.formatBalance(rate), self.coin),
            d = "You now have: `%s`%s" % (self.formatBalance(self.addToBal(ctx.author, rate)), self.coin)
        )
        await ctx.send(embed=embed)
    
    @cur.command()
    @commands.cooldown(1, 3600 * 24 * 7, commands.BucketType.user)
    async def weekly(self, ctx: commands.Context):
        """
        Claim your daily Coins!
        """
        rate = int(os.getenv("WEEKLY_CUR_RATE"))
        embed = fmte(
            ctx,
            t = "`%s`%s Gained!" % (self.formatBalance(rate), self.coin),
            d = "You now have: `%s`%s" % (self.formatBalance(self.addToBal(ctx.author, rate)), self.coin)
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def manualadd(self, ctx: commands.Context, user: Optional[discord.User], amount: Optional[int] = 1000):
        self.addToBal(user or ctx.author, amount)

    @commands.command()
    @commands.is_owner()
    async def manualset(self, ctx: commands.Context, user: Optional[discord.User], amount: Optional[int]):
        self.setBal(user or ctx.author, amount)

    @commands.command()
    @commands.is_owner()
    async def manualdel(self, ctx: commands.Context, user: Optional[discord.User]):
        self.tab.delete(conditions=["userid=%s" % (user or ctx.author).id])

    def clamp(
            self,
            value: int,
            lower_bound: int = None,
            upper_bound: int = None):
        lower_bound = lower_bound or value
        upper_bound = upper_bound or value
        return max([min([value, upper_bound]), lower_bound])

    async def cine(self, user: discord.User, newbal: int = 0):
        if not self.tab.select(conditions="userid=%s" % user.id):
            self.tab.insert(values=[self.user.id, newbal])
            self.tab.commit()

    def formatBalance(self, bal: int):
        return "".join(["%s," % char if c % 3 == 0 else char for c,
                       char in enumerate(str(bal)[::-1])][::-1]).strip(",")

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

    def setBal(self, user: discord.User, amount: int):
        """
        Sets the user's current balance
        """
        self.cine(user)
        self.tab.update(
            values=[
                "balance=%s" %
                str(amount)],
            conditions=[
                "userid = %s" %
                user.id])
        self.tab.commit()

    def addToBal(self, user: discord.User, amount: int) -> int:
        """
        Adds an amount of currency to a user's balance
        ## Returns
        The user's new balance
        """
        v = self.getUserBal(user)
        self.tab.update(
            values=[
                "balance=%s" % str(
                    v + amount)],
            conditions=[
                "userid = %s" % user.id])
        self.tab.commit()
        return v + amount


class GiveView(discord.ui.View):
    def __init__(self, bot, ctx, amount, auth, user):
        self.bot: commands.AutoShardedBot = bot
        self.ctx: commands.Context = ctx
        self.amount: int = amount
        self.auth: discord.User = auth
        self.user: discord.User = user
        super().__init__()


    @discord.ui.button(label="Accept", emoji="✅",
                       style=discord.ButtonStyle.primary)
    async def ack(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.auth:
            await inter.response.send_message("This is not your interaction.")
            return
        inst = Currency(self.bot)
        authnew = inst.addToBal(self.auth, -self.amount)
        usernew = inst.addToBal(self.user, self.amount)
        embed = fmte(
            self.ctx,
            t=f"Transaction Completed\nTransferred `{self.amount}`{inst.coin} from `{self.auth.display_name}` to `{self.user.display_name}`",
            d=f"**`{self.auth}` balance:** `{authnew}`{inst.coin}\n**`{self.user}` balance:** `{usernew}`{inst.coin}"
        )
        await inter.response.edit_message(content=None, embed=embed, view=None)

    @discord.ui.button(label="Decline", emoji="❌",
                       style=discord.ButtonStyle.danger)
    async def dec(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.auth:
            await inter.response.send_message("This is not your interaction.")
            return
        embed = fmte(
            self.ctx,
            t="Transaction Declined",
            d="No currency has been transfered."
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
        self.auth: discord.User = auth
        self.user: discord.User = user
        super().__init__()

    @discord.ui.button(label="Accept", emoji="✅",
                       style=discord.ButtonStyle.primary)
    async def ack(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.user:
            await inter.response.send_message("This is not your interaction.")
            return
        inst = Currency(self.bot)
        authnew = inst.addToBal(self.auth, self.amount)
        usernew = inst.addToBal(self.user, -self.amount)
        embed = fmte(
            self.ctx,
            t=f"Transaction Completed\nTransferred `{self.amount}`{inst.coin} from `{self.auth.display_name}` to `{self.user.display_name}`",
            d=f"**`{self.auth}` balance:** `{authnew}`{inst.coin}\n**`{self.user}` balance:** `{usernew}`{inst.coin}"
        )
        await inter.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Decline", emoji="❌",
                       style=discord.ButtonStyle.danger)
    async def dec(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.user:
            await inter.response.send_message("This is not your interaction.")
            return
        embed = fmte(
            self.ctx,
            t="Transaction Declined",
            d="No currency has been transfered."
        )
        for c in self.children:
            c.disabled = True
        await inter.response.edit_message(embed=embed, view=None)

    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True


class LeaderboardView(discord.ui.View):
    def __init__(self,
                 bot: commands.Bot,
                 ephemeral: bool,
                 values: Mapping[discord.User,
                                 int],
                 pagesize: int,
                 *,
                 timeout: Optional[float] = 180,
                 ):
        self.bot = bot
        self.ephemeral = ephemeral
        self.vals = [v for v in sorted(
            list(
                values.items()),
            key=lambda v: v[1],
            reverse=True) if v[1] != 0]
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
        for c, t in enumerate(
                self.vals[self.pagesize * (self.pos - 1):self.pagesize * (self.pos)]):
            user, bal = t[0], t[1]
            embed.add_field(
                name="{}: {}".format((c + 1) + (self.pos - 1) * self.pagesize, user),
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
