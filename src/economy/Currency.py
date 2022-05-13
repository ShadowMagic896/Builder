import math
import os
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

import random
from typing import Any, List, Mapping, Optional, Union

import pymongo
from pymongo.database import Database
from pymongo.collection import Collection

from auxiliary.Embeds import fmte, fmte_i
from botAuxiliary.Constants import CONSTANTS


class Currency(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.coin = CONSTANTS.Emojis().COIN_ID

    def ge(self):
        return "\N{MONEY BAG}"

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

        db = BalanceDatabase(ctx)
        balance = await db.getBalance(user)
        
        f_balance = self.formatBalance(balance)

        embed = fmte(
            ctx, 
            t=f"`{user}`'s Balance: `{f_balance}`{self.coin}"
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
        db = BalanceDatabase(ctx)
        if (cv := (await db.getBalance(ctx.author))) < amount:
            raise ValueError("You don't have that much money!")

        embed = fmte(
            ctx,
            t=f"Are You Sure You Want to Give `{self.formatBalance(amount)}`{self.coin} to `{user}`?",
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

        db = BalanceDatabase(ctx)
        if (cv := await db.getBalance(user)) < amount:
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
        db = BalanceDatabase(ctx)
        amount = random.randint(max(-500, -await db.getBalance(ctx.author)), 1000)
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

        db = BalanceDatabase(ctx)
        await db.addToBalance(ctx.author, amount)
        
        sign = "+" if amount >= 0 else ""
        f_amt = self.formatBalance(amount)
        embed = fmte(
            ctx,
            t=f"`{sign}{f_amt}`{self.coin}",
            d=k
        )
        await ctx.send(embed=embed)

    @cur.command()
    # @commands.cooldown(1, 60, commands.BucketType.user)
    async def leaderboard(self, ctx: commands.Context):
        """
        See who's the wealthiest in this server
        """
        db = BalanceDatabase(ctx)
        data = await db.leaderboard(ctx.guild.members)
        values = [{ctx.guild.get_member(entry["userid"]): entry["balance"]} for entry in data]
        # print(f"Sending Values: {values}")
        view = LeaderboardView(ctx, values, 5)
        embed = view.page_zero(ctx.interaction)
        view.checkButtons()
        await ctx.send(embed=embed, view=view)

    @cur.command()
    @commands.cooldown(3, 120, commands.BucketType.user)
    @describe(
        user="The user to steal from",
        amount="How to to attempt to steal"
    )
    async def steal(self, ctx: commands.Context, user: discord.User, amount: int):
        """
        Attempts to steal money from a user. You may gain some, but you may also lose some!
        """
        if user.bot:
            raise TypeError("Cannot steal from bots!")
        if user == ctx.author:
            raise ValueError("Cannot steal from yourself!")

        db = BalanceDatabase(ctx)
        auth_bal = await db.getBalance(ctx.author)
        user_bal = await db.getBalance(user)

        if amount > auth_bal:
            raise ValueError("You cannot risk more than you own!")
        if amount > user_bal:
            raise ValueError("You cannot steal more than they own!")
        if amount < 1:
            raise ValueError("Invalid Amount")
        chnc = 0.60

        success = random.random() < chnc
        db = BalanceDatabase(ctx)
        if success:
            na = await db.addToBalance(ctx.author, amount)
            nu = await db.addToBalance(user, -amount)
            
            f_amt = self.formatBalance(amount)

            fmt_ao = self.formatBalance(auth_bal)
            fmt_uo = self.formatBalance(user_bal)

            fmt_an = self.formatBalance(na)
            fmt_un = self.formatBalance(nu)


            embed = fmte(
                ctx,
                t=f"Successful! You Stole `{f_amt}`{self.coin}.",
                d=f"**You Now Have:** `{fmt_an}`{self.coin} [Before: `{fmt_ao}`{self.coin}]\n**{user.name} Now Has:** `{fmt_un}`{self.coin} [Before: `{fmt_uo}`{self.coin}]"
            )
            await ctx.send(embed=embed)
            embed = fmte(
                ctx,
                t=f"`{f_amt}`{self.coin} Were Stolen From You!",
                d=f"**Guild:** `{ctx.guild}`\n**User:** `{ctx.author}`"
            )
            await user.send(embed=embed)
        else:
            na = await db.addToBalance(ctx.author, -amount)
            nu = await db.addToBalance(user, amount)
            
            f_amt = self.formatBalance(amount)

            fmt_ao = self.formatBalance(auth_bal)
            fmt_uo = self.formatBalance(user_bal)

            fmt_an = self.formatBalance(na)
            fmt_un = self.formatBalance(nu)


            embed = fmte(
                ctx,
                t=f"Failure! You Lost `{f_amt}`{self.coin}.",
                d=f"**You Now Have:** `{fmt_an}`{self.coin} [Before: `{fmt_ao}`{self.coin}]\n**{user.name} Now Has:** `{fmt_un}`{self.coin} [Before: `{fmt_uo}`{self.coin}]"
            )
            await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def hourly(self, ctx: commands.Context):
        """
        Claim your hourly Coins!
        """
        rate = CONSTANTS.Rates().HOURLY
        _rate = self.formatBalance(rate)

        db = BalanceDatabase(ctx)
        balance = await db.addToBalance(ctx.author, rate)
        
        _balance = self.formatBalance(balance)

        embed = fmte(
            ctx, 
            t=f"`{_rate}`{self.coin} Gained!",
            d=f"You now have: `{_balance}`{self.coin}"
        )
        await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(1, 3600 * 24, commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        """
        Claim your daily Coins!
        """
        rate = CONSTANTS.Rates().DAILY
        _rate = self.formatBalance(rate)

        db = BalanceDatabase(ctx)
        balance = await db.addToBalance(ctx.author, rate)
        
        _balance = self.formatBalance(balance)

        embed = fmte(
            ctx, 
            t=f"`{_rate}`{self.coin} Gained!",
            d=f"You now have: `{_balance}`{self.coin}"
        )
        await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(1, 3600 * 24 * 7, commands.BucketType.user)
    async def weekly(self, ctx: commands.Context):
        """
        Claim your daily Coins!
        """
        rate = CONSTANTS.Rates().WEEKLY
        _rate = self.formatBalance(rate)

        db = BalanceDatabase(ctx)
        balance = await db.addToBalance(ctx.author, rate)

        _balance = self.formatBalance(balance)

        embed = fmte(
            ctx, 
            t=f"`{_rate}`{self.coin} Gained!",
            d=f"You now have: `{_balance}`{self.coin}"
        )
        await ctx.send(embed=embed)

    @cur.command()
    async def quiz(self, ctx: commands.Context):
        embed = fmte(
            ctx,
            t="Select Options",
            d="Once you are finished, press `Start`"
        )
        view = StartQuizView(ctx)
        await ctx.send(embed=embed, view=view)

    # @cur.command()
    # @commands.is_owner()
    async def manualadd(self, ctx: commands.Context, user: Optional[discord.User], amount: Optional[int] = 1000):
        db = BalanceDatabase(ctx)
        await db.addToBalance(user or ctx.author, amount)

    # @cur.command()
    # @commands.is_owner()
    async def manualset(self, ctx: commands.Context, user: Optional[discord.User], amount: Optional[int]):
        db = BalanceDatabase(ctx)
        await db.setBalance(user or ctx.author, amount)

    # @cur.command()
    # @commands.is_owner()
    async def manualdel(self, ctx: commands.Context, user: Optional[discord.User]):
        db = BalanceDatabase(ctx)
        await db.delete(user or ctx.author)

    def clamp(
            self,
            value: int,
            lower_bound: int = None,
            upper_bound: int = None):
        lower_bound = lower_bound or value
        upper_bound = upper_bound or value
        return max([min([value, upper_bound]), lower_bound])

    def formatBalance(self, bal: int):
        return "".join(["%s," % char if c % 3 == 0 else char for c,
                       char in enumerate(str(bal)[::-1])][::-1]).strip(",")


class GiveView(discord.ui.View):
    def __init__(self, bot, ctx, amount, auth, user):
        self.bot: commands.AutoShardedBot = bot
        self.amount: int = amount
        self.auth: discord.User = auth
        self.ctx: commands.Context = ctx
        self.user: discord.User = user
        super().__init__()

    @discord.ui.button(label="Accept", emoji="\N{WHITE HEAVY CHECK MARK}",
                       style=discord.ButtonStyle.primary)
    async def ack(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.auth:
            await inter.response.send_message("This is not your interaction.")
            return

        db = BalanceDatabase(self.ctx)
        authnew = await db.addToBalance(self.auth, -self.amount)
        usernew = await db.addToBalance(self.user, self.amount)
        coin = CONSTANTS.Emojis().COIN_ID
        f = Currency(self.ctx).formatBalance

        embed = fmte(
            self.ctx,
            t=f"Transaction Completed\nTransferred `{f(self.amount)}`{coin} from `{self.auth.display_name}` to `{self.user.display_name}`",
            d=f"**`{self.auth}` balance:** `{f(authnew)}`{coin}\n**`{self.user}` balance:** `{f(usernew)}`{coin}")
        await inter.response.edit_message(content=None, embed=embed, view=None)

    @discord.ui.button(label="Decline", emoji="\N{CROSS MARK}",
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

    @discord.ui.button(label="Accept", emoji="\N{WHITE HEAVY CHECK MARK}",
                       style=discord.ButtonStyle.primary)
    async def ack(self, inter: discord.Interaction, button: discord.Button):
        if inter.user != self.user:
            await inter.response.send_message("This is not your interaction.")
            return
        
        db = BalanceDatabase(self.ctx)
        authnew = await db.addToBalance(self.auth, self.amount)
        usernew = await db.addToBalance(self.user, -self.amount)
        coin = CONSTANTS.Emojis().COIN_ID
        f = Currency(self.ctx).formatBalance
        embed = fmte(
            self.ctx,
            t=f"Transaction Completed\nTransferred `{f(self.amount)}`{coin} from `{self.auth.display_name}` to `{self.user.display_name}`",
            d=f"**`{self.auth}` balance:** `{f(authnew)}`{coin}\n**`{self.user}` balance:** `{f(usernew)}`{coin}")
        await inter.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Decline", emoji="\N{CROSS MARK}",
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
    def __init__(self, ctx: commands.Context, values: Mapping[discord.User, int], pagesize: int, *,
                 timeout: Optional[float] = 180):
        self.ctx = ctx
        self.pagesize = pagesize

        self.pos = 1

        self.vals = values
        
        self.maxpos = math.ceil((len(self.vals) / pagesize))

        super().__init__(timeout=timeout)

    @discord.ui.button(emoji=CONSTANTS.Emojis().BBARROW_ID, custom_id="bb")
    async def fullback(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos = 1
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=CONSTANTS.Emojis().BARROW_ID, custom_id="b")
    async def back(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos -= 1
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="\N{CROSS MARK}", style=discord.ButtonStyle.red, custom_id="x")
    async def close(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        await inter.message.delete()

    @discord.ui.button(emoji=CONSTANTS.Emojis().FARROW_ID, custom_id="f")
    async def next(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos += 1
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji=CONSTANTS.Emojis().FFARROW_ID, custom_id="ff")
    async def fullnext(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos = self.maxpos
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.checkButtons(button)

        embed = self.add_fields(self.embed(inter))
        await inter.response.edit_message(embed=embed, view=self)

    def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter,
            t="Leaderboard: Page `{}` of `{}`".format(self.pos, self.maxpos)
        )

    def add_fields(self, embed: discord.Embed):
        _slice = self.vals[self.pagesize * (self.pos - 1):self.pagesize * (self.pos)]
        for place, entry in enumerate(_slice):
            user, bal = list(entry.keys())[0], list(entry.values())[0]
            f_bal = Currency(self.ctx.bot).formatBalance(bal)
            embed.add_field(
                name=f"{place + 1 + (self.pos - 1) * self.pagesize}: {user}",
                value=f"`{f_bal}`",
                inline=False
            )
        return embed

    def page_zero(self, interaction: discord.Interaction):
        self.pos = 1
        return self.add_fields(self.embed(interaction))

    def checkButtons(self, button: discord.Button = None):
        if self.maxpos <= 1:
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


class StartQuizView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.dif = None
        self.cat = None
        self.questions = None
        super().__init__()

    @discord.ui.select(
        placeholder="Please choose a difficulty...",
        options=[
            discord.SelectOption(
                label=x,
                value=x) for x in [
                "Easy",
                "Medium",
                "Hard"]])
    async def dif(self, inter: discord.Interaction, _: Any):
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.dif = inter.data["values"][0]
        await self.sil(inter)

    @discord.ui.select(
        placeholder="Please choose a category...",
        options=[
            discord.SelectOption(
                label=x,
                value=x) for x in [
                "Linux",
                "Bash",
                "Docker",
                "SQL",
                "CMS",
                "Code",
                "DevOps"]])
    async def cat(self, inter: discord.Interaction, _: Any):
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        self.cat = inter.data["values"][0]
        await self.sil(inter)

    @discord.ui.button(emoji="\N{BLACK RIGHTWARDS ARROW}", label="Start",
                       style=discord.ButtonStyle.green,)
    async def start(self, inter: discord.Interaction, _: Any):
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        if self.dif is not None and self.cat is not None:
            key = os.getenv("QUIZAPI_KEY")
            url = f"https://quizapi.io/api/v1/questions?apiKey={key}&category={self.cat}&difficulty={self.dif}&limit=5"
            self.questions = await (await self.ctx.bot.session.get(url)).json()
            view = MainQuizView(
                self.questions,
                self.cat,
                self.dif,
                self.ctx)
            s = QuizAnsSelect(self.questions[0], self.ctx)
            view.add_item(s)
            view.add_item(QuizQuestionSubmit(view, s))
            view.add_item(QuizClose(self.ctx))
            embed = view.embed(self.ctx)
            await inter.response.edit_message(embed=embed, view=view)

    @discord.ui.button(style=discord.ButtonStyle.danger,
                       label="Close", emoji="\N{CROSS MARK}")
    async def close(self, inter: discord.Interaction, _: Any) -> Any:
        if inter.user != self.ctx.author:
            await inter.response.send_message("You are not the owner of this interaction", ephemeral=True)
            return
        await inter.message.delete()

    async def sil(self, inter: discord.Interaction):
        try:
            await inter.response.send_message()
        except BaseException:
            pass


class MainQuizView(discord.ui.View):
    def __init__(
            self,
            questions: List[dict],
            cat: str,
            dif: str,
            ctx,
            *,
            timeout: Optional[float] = 180):
        self.pos = 1
        self.maxpos = 5
        self.questions = questions
        self.cat = cat
        self.dif = dif
        self.ctx = ctx

        # [Question, Chosen Option, Correct Answers, Correct Bool, Readable Chosen Option, Readable Correct Answers]
        self.selected: List[List[str, str,
                                 List[str], bool, str, List[str]]] = []

        super().__init__(timeout=timeout)

    def embed(self, ctx_or_inter):
        q = self.questions[self.pos - 1]
        if isinstance(ctx_or_inter, commands.Context):
            return fmte(
                ctx_or_inter,
                t="Question `{}`:\n{}".format(self.pos, q["question"]),
                d="Category: `{}`\nDifficulty: `{}`".format(self.cat, self.dif)
            )
        else:
            return fmte_i(
                ctx_or_inter,
                t="Question `{}`:\n{}".format(self.pos, q["question"]),
                d="Category: `{}`\nDifficulty: `{}`".format(self.cat, self.dif)
            )


class QuizAnsSelect(discord.ui.Select):
    def __init__(self, question: dict, ctx):
        self.ctx = ctx
        self.qname = question["question"]
        self.description = question["description"]
        self.ops = [discord.SelectOption(label=x[1][:100], value=x[0]) for x in list(
            question["answers"].items()) if x[1] is not None]
        self.correct = [
            k[:-8] for k, v in list(question["correct_answers"].items()) if v != "false"]
        self.correct_readable = [v for k, v in list(
            question["answers"].items()) if k in self.correct]
        super().__init__(placeholder="Please choose an answer!", options=self.ops)

    def getValueReadable(self, val):
        return [c.label for c in self.ops if c.value == val][0]

    async def callback(self, interaction: discord.Interaction) -> Any:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You are not taking this quiz!", ephemeral=True)
            return
        try:
            await interaction.response.send_message()
        except BaseException:
            pass


class QuizQuestionSubmit(discord.ui.Button):
    def __init__(self, view: discord.ui.View, select: discord.ui.Select):
        self._view = view
        self.ctx: commands.Context = self._view.ctx
        self.select = select
        super().__init__(style=discord.ButtonStyle.green, emoji="\N{BLACK RIGHTWARDS ARROW}", label="Submit")

    async def callback(self, interaction: discord.Interaction) -> Any:
        if not self.select.values:
            return
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You are not taking this quiz!", ephemeral=True)
            return
        # [Question, Chosen Option, Correct Answers, Correct Bool, Readable Chosen Option, Readable Correct Answers]
        self._view.selected.append([self.select.qname,
                                    self.select.values[0],
                                    self.select.correct,
                                    self.select.values[0] in self.select.correct,
                                    self.select.getValueReadable(self.select.values[0]),
                                    [self.select.getValueReadable(x) for x in self.select.correct]])
        self._view.pos += 1
        if self._view.pos == self._view.maxpos + 1:
            cc = [x for x in self._view.selected]
            jr = ", ".join
            desc = "\n".join(
                [
                    f"ㅤ**Question:** *\"{entry[0]}\"*\nㅤ**Response:** {entry[4]}\nㅤ**Answer[s]:** {jr(entry[5])}\n" for entry in self._view.selected
                ]
            )
            cor = [x[3] for x in cc].count(True)
            tot = len(self._view.selected)
            per = (cor / tot) * 100
            score = f"\n`{cor} / {tot} [{per}%]`"

            base_winnings = 5000
            mults = {
                "Easy": 0.75,
                "Medium": 1,
                "Hard": 1.25
            }
            perc = round(base_winnings * mults[self._view.dif] * ([x[3]
                         for x in cc].count(True) / self._view.maxpos))
            formatted = Currency(self.ctx.bot).formatBalance(perc)

            coin = CONSTANTS.Emojis().COIN_ID
            embed = fmte_i(
                interaction,
                t=f"Quiz Finished! You Earned `{formatted}`{coin}!\nCategory: `{self._view.cat}`\nDifficulty: `{self._view.dif}`",
                d=f"**Results:**\n{desc}{score}"
            )

            db = BalanceDatabase(self.ctx)
            await db.addToBalance(self.ctx.author, perc)

            await interaction.response.edit_message(embed=embed, view=None)
        else:
            # print(self._view.pos, self.select.values)
            question = self._view.questions[self._view.pos - 1]
            embed = self._view.embed(interaction)
            view = MainQuizView(
                self._view.questions,
                self._view.cat,
                self._view.dif,
                self._view.ctx)
            view.pos = self._view.pos
            view.selected = self._view.selected

            s = QuizAnsSelect(question, self._view.ctx)
            view.add_item(s)
            view.add_item(QuizQuestionSubmit(view, s))
            view.add_item(QuizClose(self._view.ctx))

            await interaction.response.edit_message(embed=embed, view=view)


class QuizClose(discord.ui.Button):
    def __init__(self, ctx):
        self.ctx = ctx
        super().__init__(style=discord.ButtonStyle.danger, label="Close", emoji="\N{CROSS MARK}")

    async def callback(self, interaction: discord.Interaction) -> Any:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You are not taking this quiz!")
            return
        await interaction.message.delete()


class BalanceDatabase:
    def __init__(self, ctx: commands.Context):
        self.bot: commands.Bot = ctx.bot
        self.database: Database = self.bot.database
        self.collections: Mapping[str, Collection] = self.bot.collections
    
    async def checkForExist(self, user: discord.User, default_value: int = 0) -> bool:
        """
        Checks for a user's existence in the database. If it is not there, it creates a new entry with the ID of the user and the value of defualt_value.
        Returns whether a new entry was created.
        """
        if self.collections["balances"].find_one({"userid": user.id}) is None:
            self.collections["balances"].insert_one({"userid": user.id, "balance": default_value})
            return True
        return False
    
    async def addToBalance(self, user: discord.User, value: int) -> int:
        """
        Updates a user's balance.
        Returns the user's new balance.
        """
        result = self.collections["balances"].find_one_and_update({"userid": user.id}, {"$inc": {"balance": value}}, upsert=True, return_document=True)
        return result["balance"]
    
    async def setBalance(self, user: discord.User, value: int) -> None:
        """
        Sets a user's balance.
        """
        self.collections["balances"].replace_one(
            filter={"userid": user.id}, 
            replacement={"$set": {"balance": value}}, 
            upsert=True
        )

    async def getBalance(self, user: discord.User) -> int:
        """
        Gets a user's balance.
        """
        result = self.collections["balances"].find_one({"userid": user.id})
        if result is None:
            result = self.collections["balances"].insert_one({"userid": user.id, "balance": 0})
            value = 0
        else:
            value = result["balance"]
        return value
    
    async def delete(self, user: discord.User) -> None:
        """
        Deletes a user's entry
        """
        self.collections["balances"].delete_one({"userid": user.id})
    
    async def leaderboard(self, members: List[Union[discord.Member, discord.User]]) -> Mapping[int, int]:
        """
        Returns a sorted list of {UserID: Balance}
        """
        ids = [member.id for member in members]
        _values = self.collections["balances"].find({"userid": {"$in": ids}})
        # print([x for x in _values.clone()])
        values = _values.sort("balance", pymongo.DESCENDING)
        # print([x for x in values.clone()])
        return values.clone()

async def setup(bot):
    await bot.add_cog(Currency(bot))
