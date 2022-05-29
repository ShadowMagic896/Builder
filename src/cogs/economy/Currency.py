import asyncpg
import discord
from discord import Interaction, app_commands
from discord.app_commands import describe, Range
from discord.ext import commands

import random
from typing import Any, List, Mapping, Optional, Union
from data.config import Config

from src.auxiliary.user.Embeds import fmte, fmte_i
from src.auxiliary.bot.Constants import CONSTANTS
from src.auxiliary.user.Subclass import BaseModal, BaseView, Paginator


class Currency(commands.Cog):
    """
    Get bank
    """

    def __init__(self, bot: commands.Bot, add_commands: bool = False):
        self.bot = bot
        self.coin = CONSTANTS.Emojis().COIN_ID
        if add_commands:
            self.bot.tree.add_command(
                app_commands.ContextMenu(
                    name="\N{MONEY BAG} Give Money", callback=self.giveMenu
                )
            )
            self.bot.tree.add_command(
                app_commands.ContextMenu(
                    name="\N{MONEY BAG} Request Money", callback=self.requestMenu
                )
            )

    def ge(self):
        return "\N{MONEY BAG}"

    @commands.hybrid_group()
    async def cur(self, ctx: commands.Context):
        pass

    @cur.command()
    @commands.cooldown(2, 15, commands.BucketType.user)
    @describe(user="The user to get the balance of")
    async def balance(self, ctx: commands.Context, user: Optional[discord.User]):
        """
        Returns your current balance.
        """
        user = user or ctx.author
        if user.bot:
            raise TypeError("User cannot be a bot.")

        db = BalanceDatabase(ctx)
        rec = await db.getBalance(user)

        embed = fmte(ctx, t=f"`{user}`'s Balance: `{rec:,}`{self.coin}")
        await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(2, 30, commands.BucketType.user)
    @describe(user="The user to give money to", amount="How much money to give")
    async def give(
        self, ctx: commands.Context, user: discord.User, amount: Range[int, 1]
    ):
        """
        Sends money to a user.
        """
        if user.bot:
            raise TypeError("User cannot be a bot.")
        db = BalanceDatabase(ctx)
        if (cv := (await db.getBalance(ctx.author))) < amount:
            raise ValueError("You don't have that much money!")

        embed = fmte(
            ctx,
            t=f"Are You Sure You Want to Give `{amount:,}`{self.coin} to `{user}`?",
            d=f"This is `{round((amount / cv) * 100, 2)}%` of your money.",
        )
        await ctx.send(embed=embed, view=GiveView(ctx, amount, ctx.author, user))

    @cur.command()
    @commands.cooldown(2, 120, commands.BucketType.user)
    @describe(user="The user to request money from", amount="How much money to request")
    async def request(
        self, ctx: commands.Context, user: discord.User, amount: Range[int, 1]
    ):
        """
        Requests money from a user.
        """
        if user.bot:
            raise TypeError("User cannot be a bot.")
        perms = ctx.channel.permissions_for(user)
        if not (perms.read_message_history or perms.read_messages):
            raise TypeError("That user cannot see this channel.")

        db = BalanceDatabase(ctx)
        if (cv := (await db.getBalance(user))) < amount:
            raise ValueError("They don't have that much money!")

        embed = fmte(
            ctx,
            t=f"`{user}`, Do You Want to Give `{ctx.author}` `{amount}`{self.coin}?",
            d=f"This is `{round((amount / cv) * 100, 2)}%` of your money.",
        )

        view = RequestView(ctx, amount, ctx.author, user)
        message = await ctx.send(
            user.mention, embed=embed, view=RequestView(ctx, amount, ctx.author, user)
        )
        view.message = message

    @cur.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def beg(self, ctx: commands.Context):
        """
        Begs for money. You can win some, but you can also lose some.
        """
        db = BalanceDatabase(ctx)
        amount = random.randint(max(-500, -await db.getBalance(ctx.author)), 1000)
        if amount < 0:
            k = random.choice(
                [
                    "Some villain saw you begging and mugged you. Sucks to suck.",
                    "You tripped on the curb and somehow lost your wallet. Nice job...",
                    "You ate the coins. For some reason.",
                ]
            )
        elif amount > 0:
            k = random.choice(
                [
                    "You saw someone begging and decied to mug them. You villain!",
                    "Some buffoon left some coins out on the road, might as well keep them for good fortune.",
                    "You found some coins in the toilet... why were you looking there!?",
                ]
            )
        else:
            k = "You did nothing, and nothing happened."

        db = BalanceDatabase(ctx)
        await db.addToBalance(ctx.author, amount)

        sign = "+" if amount >= 0 else ""
        embed = fmte(ctx, t=f"`{sign}{amount:,}`{self.coin}", d=k)
        await ctx.send(embed=embed)

    @cur.command()
    # @commands.cooldown(1, 60, commands.BucketType.user)
    async def leaderboard(self, ctx: commands.Context):
        """
        See who's the wealthiest in this server.
        """
        db = BalanceDatabase(ctx)
        data = await db.leaderboard(ctx.guild.members)
        values = [
            {ctx.guild.get_member(entry["userid"]): entry["balance"]} for entry in data
        ]
        view = LeaderboardView(ctx, values, 5)
        embed = await view.page_zero(ctx.interaction)
        await view.checkButtons()
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @cur.command()
    @commands.cooldown(3, 120, commands.BucketType.user)
    @describe(user="The user to steal from", amount="How to to attempt to steal")
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
            na = (await db.addToBalance(ctx.author, amount))["balance"]
            nu = (await db.addToBalance(user, -amount))["balance"]

            embed = fmte(
                ctx,
                t=f"Successful! You Stole `{amount:,}`{self.coin}.",
                d=f"**You Now Have:** `{na:,}`{self.coin} [Before: `{auth_bal:,}`{self.coin}]\n**{user.name} Now Has:** `{nu:,}`{self.coin} [Before: `{user_bal:,}`{self.coin}]",
            )
            await ctx.send(embed=embed)
            embed = fmte(
                ctx,
                t=f"`{amount:,}`{self.coin} Were Stolen From You!",
                d=f"**Guild:** `{ctx.guild}`\n**User:** `{ctx.author}`",
            )
            await user.send(embed=embed)
        else:
            na = (await db.addToBalance(ctx.author, -amount))["balance"]
            nu = (await db.addToBalance(user, amount))["balance"]

            embed = fmte(
                ctx,
                t=f"Failure! You Lost `{amount:,}`{self.coin}.",
                d=f"**You Now Have:** `{na:,}`{self.coin} [Before: `{auth_bal:,}`{self.coin}]\n**{user.name} Now Has:** `{nu:,}`{self.coin} [Before: `{user_bal:,}`{self.coin}]",
                c=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def hourly(self, ctx: commands.Context):
        """
        Claim your hourly Coins!
        """
        rate = CONSTANTS.Rates().HOURLY

        db = BalanceDatabase(ctx)
        balance = (await db.addToBalance(ctx.author, rate))["balance"]

        embed = fmte(
            ctx,
            t=f"`{rate:,}`{self.coin} Gained!",
            d=f"You now have: `{balance:,}`{self.coin}",
        )
        await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(1, 3600 * 24, commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        """
        Claim your daily Coins!
        """
        rate = CONSTANTS.Rates().DAILY

        db = BalanceDatabase(ctx)
        balance = (await db.addToBalance(ctx.author, rate))["balance"]

        embed = fmte(
            ctx,
            t=f"`{rate:,}`{self.coin} Gained!",
            d=f"You now have: `{balance:,}`{self.coin}",
        )
        await ctx.send(embed=embed)

    @cur.command()
    @commands.cooldown(1, 3600 * 24 * 7, commands.BucketType.user)
    async def weekly(self, ctx: commands.Context):
        """
        Claim your daily Coins!
        """
        rate = CONSTANTS.Rates().WEEKLY

        db = BalanceDatabase(ctx)
        balance = (await db.addToBalance(ctx.author, rate))["balance"]

        embed = fmte(
            ctx,
            t=f"`{rate:,}`{self.coin} Gained!",
            d=f"You now have: `{balance:,}`{self.coin}",
        )
        await ctx.send(embed=embed)

    @cur.command()
    async def quiz(self, ctx: commands.Context):
        embed = fmte(ctx, t="Select Options", d="Once you are finished, press `Start`")
        view = StartQuizView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    # @cur.command()
    # @commands.is_owner()
    async def manualadd(
        self,
        ctx: commands.Context,
        user: Optional[discord.User],
        amount: Optional[int] = 1000,
    ):
        db = BalanceDatabase(ctx)
        await db.addToBalance(user or ctx.author, amount)

    # @cur.command()
    # @commands.is_owner()
    async def manualset(
        self, ctx: commands.Context, user: Optional[discord.User], amount: Optional[int]
    ):
        db = BalanceDatabase(ctx)
        await db.setBalance(user or ctx.author, amount)

    # @cur.command()
    # @commands.is_owner()
    async def manualdel(self, ctx: commands.Context, user: Optional[discord.User]):
        db = BalanceDatabase(ctx)
        await db.delete(user or ctx.author)

    async def giveMenu(self, inter: discord.Interaction, member: discord.Member):
        ctx: commands.Context = await commands.Context.from_interaction(inter)
        ctx.author = inter.user
        await inter.response.send_modal(GiveContextModal(ctx, member))

    async def requestMenu(self, inter: discord.Interaction, member: discord.Member):
        ctx: commands.Context = await commands.Context.from_interaction(inter)
        ctx.author = inter.user
        await inter.response.send_modal(RequestContextModal(ctx, member))

    def clamp(self, value: int, lower_bound: int = None, upper_bound: int = None):
        lower_bound = lower_bound or value
        upper_bound = upper_bound or value
        return max([min([value, upper_bound]), lower_bound])


class GiveContextModal(BaseModal):
    def __init__(self, ctx: commands.Context, member: discord.Member):
        self.ctx = ctx
        self.member = member
        super().__init__(ctx, title=f"Give Coins to {member}")

    amount = discord.ui.TextInput(label="How Much Would You Like to Give?")

    async def on_submit(self, interaction: Interaction) -> None:
        try:
            amount = int(self.amount.value)
        except TypeError:
            raise commands.errors.UserInputError("Not a valid amount")
        self.ctx.interaction = interaction
        return await Currency.give.callback(
            Currency(self.ctx.bot), self.ctx, self.member, amount
        )


class RequestContextModal(BaseModal):
    def __init__(self, ctx: commands.Context, member: discord.Member):
        self.ctx = ctx
        self.member = member
        super().__init__(title=f"Request Coins from {member}")

    amount = discord.ui.TextInput(label="How Much Would You Like to Request?")

    async def on_submit(self, interaction: Interaction) -> None:
        try:
            amount = int(self.amount.value)
        except TypeError:
            raise commands.errors.UserInputError("Not a valid amount")
        self.ctx.interaction = interaction
        return await Currency.request.callback(
            Currency(self.ctx.bot), self.ctx, self.member, amount
        )


class GiveView(BaseView):
    def __init__(self, ctx, amount, auth, user):
        self.amount: int = amount
        self.auth: discord.User = auth
        self.ctx: commands.Context = ctx
        self.user: discord.User = user
        super().__init__(ctx)

    @discord.ui.button(
        label="Accept",
        emoji="\N{WHITE HEAVY CHECK MARK}",
        style=discord.ButtonStyle.primary,
    )
    async def ack(self, inter: discord.Interaction, button: discord.Button):

        db = BalanceDatabase(self.ctx)
        authnew = (await db.addToBalance(self.auth, -self.amount))["balance"]
        usernew = (await db.addToBalance(self.user, self.amount))["balance"]
        coin = CONSTANTS.Emojis().COIN_ID

        embed = fmte(
            self.ctx,
            t=f"Transaction Completed\nTransferred `{self.amount:,}`{coin} from `{self.auth.display_name}` to `{self.user.display_name}`",
            d=f"**`{self.auth}` balance:** `{authnew:,}`{coin}\n**`{self.user}` balance:** `{usernew:,}`{coin}",
        )
        await inter.response.edit_message(content=None, embed=embed, view=None)

    @discord.ui.button(
        label="Decline", emoji="\N{CROSS MARK}", style=discord.ButtonStyle.danger
    )
    async def dec(self, inter: discord.Interaction, button: discord.Button):
        embed = fmte(
            self.ctx, t="Transaction Declined", d="No currency has been transfered."
        )
        await inter.response.edit_message(content=None, embed=embed, view=None)

    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True


class RequestView(BaseView):
    def __init__(self, ctx, amount, auth, user):
        self.ctx: commands.Context = ctx
        self.amount: int = amount
        self.auth: discord.User = auth
        self.user: discord.User = user
        super().__init__(ctx)

    @discord.ui.button(
        label="Accept",
        emoji="\N{WHITE HEAVY CHECK MARK}",
        style=discord.ButtonStyle.primary,
    )
    async def ack(self, inter: discord.Interaction, button: discord.Button):

        db = BalanceDatabase(self.ctx)
        authnew = await db.addToBalance(self.auth, self.amount)
        usernew = await db.addToBalance(self.user, -self.amount)
        coin = CONSTANTS.Emojis().COIN_ID
        embed = fmte(
            self.ctx,
            t=f"Transaction Completed\nTransferred `{self.amount:,}`{coin} from `{self.auth.display_name}` to `{self.user.display_name}`",
            d=f"**`{self.auth}` balance:** `{authnew:,}`{coin}\n**`{self.user}` balance:** `{usernew:,}`{coin}",
        )
        await inter.response.edit_message(embed=embed, view=None)

    @discord.ui.button(
        label="Decline", emoji="\N{CROSS MARK}", style=discord.ButtonStyle.danger
    )
    async def dec(self, inter: discord.Interaction, button: discord.Button):
        embed = fmte(
            self.ctx, t="Transaction Declined", d="No currency has been transfered."
        )
        await inter.response.edit_message(embed=embed, view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.user


class LeaderboardView(Paginator):
    def __init__(
        self,
        ctx: commands.Context,
        values: List[asyncpg.Record],
        pagesize: int,
        *,
        timeout: Optional[float] = 180,
    ):
        super().__init__(ctx, values, pagesize, timeout=timeout)

    async def embed(self, inter: discord.Interaction):
        return fmte_i(
            inter, t=f"Leaderboard: Page `{self.position}` of `{self.maxpos}`"
        )

    async def adjust(self, embed: discord.Embed):
        start = self.pagesize * (self.position - 1)
        stop = self.pagesize * self.position

        for place, entry in enumerate(self.vals[start:stop]):
            user, bal = list(entry.keys())[0], list(entry.values())[0]
            embed.add_field(
                name=f"{place + 1 + (self.position - 1) * self.pagesize}: {user}",
                value=f"`{bal:,}`",
                inline=False,
            )
        return embed


class StartQuizView(BaseView):
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.dif = None
        self.cat = None
        self.questions = None
        super().__init__(ctx)

    @discord.ui.select(
        placeholder="Please choose a difficulty...",
        options=[
            discord.SelectOption(label=x, value=x) for x in ["Easy", "Medium", "Hard"]
        ],
    )
    async def dif(self, inter: discord.Interaction, _: Any):
        self.dif = inter.data["values"][0]
        await self.sil(inter)

    @discord.ui.select(
        placeholder="Please choose a category...",
        options=[
            discord.SelectOption(label=x, value=x)
            for x in ["Linux", "Bash", "Docker", "SQL", "CMS", "Code", "DevOps"]
        ],
    )
    async def cat(self, inter: discord.Interaction, _: Any):
        self.cat = inter.data["values"][0]
        await self.sil(inter)

    @discord.ui.button(
        emoji="\N{BLACK RIGHTWARDS ARROW}",
        label="Start",
        style=discord.ButtonStyle.green,
    )
    async def start(self, inter: discord.Interaction, _: Any):
        if self.dif is not None and self.cat is not None:
            key = Config().QUIZAPI_KEY
            url = f"https://quizapi.io/api/v1/questions?apiKey={key}&category={self.cat}&difficulty={self.dif}&limit=5"
            self.questions = await (await self.ctx.bot.session.get(url)).json()
            view = MainQuizView(self.questions, self.cat, self.dif, self.ctx)
            s = QuizAnsSelect(self.questions[0], self.ctx)
            view.add_item(s)
            view.add_item(QuizQuestionSubmit(view, s))
            view.add_item(QuizClose(self.ctx))
            embed = view.embed(self.ctx)
            await inter.response.edit_message(embed=embed, view=view)

    @discord.ui.button(
        style=discord.ButtonStyle.danger, label="Close", emoji="\N{CROSS MARK}"
    )
    async def close(self, inter: discord.Interaction, _: Any) -> Any:
        await inter.message.delete()

    async def sil(self, inter: discord.Interaction):
        try:
            await inter.response.send_message()
        except BaseException:
            pass


class MainQuizView(BaseView):
    def __init__(
        self,
        questions: List[dict],
        cat: str,
        dif: str,
        ctx,
        *,
        timeout: Optional[float] = 180,
    ):
        self.pos = 1
        self.maxpos = 5
        self.questions = questions
        self.cat = cat
        self.dif = dif
        self.ctx = ctx

        # [Question, Chosen Option, Correct Answers, Correct Bool, Readable Chosen Option, Readable Correct Answers]
        self.selected: List[List[str, str, List[str], bool, str, List[str]]] = []

        super().__init__(ctx, timeout=timeout)

    def embed(self, ctx_or_inter):
        q = self.questions[self.pos - 1]
        if isinstance(ctx_or_inter, commands.Context):
            return fmte(
                ctx_or_inter,
                t=f"Question `{self.pos}`:\n{q['question']}",
                d=f"Category: `{self.cat}`\nDifficulty: `{self.dif}`",
            )
        else:
            return fmte_i(
                ctx_or_inter,
                t=f"Question `{self.pos}`:\n{q['question']}",
                d=f"Category: `{self.cat}`\nDifficulty: `{self.dif}`",
            )


class QuizAnsSelect(discord.ui.Select):
    def __init__(self, question: dict, ctx):
        self.ctx = ctx
        self.qname = question["question"]
        self.description = question["description"]
        self.ops = [
            discord.SelectOption(label=x[1][:100], value=x[0])
            for x in list(question["answers"].items())
            if x[1] is not None
        ]
        self.correct = [
            k[:-8] for k, v in list(question["correct_answers"].items()) if v != "false"
        ]
        self.correct_readable = [
            v for k, v in list(question["answers"].items()) if k in self.correct
        ]
        super().__init__(placeholder="Please choose an answer!", options=self.ops)

    def getValueReadable(self, val):
        return [c.label for c in self.ops if c.value == val][0]

    async def callback(self, interaction: discord.Interaction) -> Any:
        try:
            await interaction.response.send_message()
        except BaseException:
            pass


class QuizQuestionSubmit(discord.ui.Button):
    def __init__(self, view: discord.ui.View, select: discord.ui.Select):
        self._view = view
        self.ctx: commands.Context = self._view.ctx
        self.select = select
        super().__init__(
            style=discord.ButtonStyle.green,
            emoji="\N{BLACK RIGHTWARDS ARROW}",
            label="Submit",
        )

    async def callback(self, interaction: discord.Interaction) -> Any:
        if not self.select.values:
            return
        self._view.selected.append(
            [
                self.select.qname,
                self.select.values[0],
                self.select.correct,
                self.select.values[0] in self.select.correct,
                self.select.getValueReadable(self.select.values[0]),
                [self.select.getValueReadable(x) for x in self.select.correct],
            ]
        )
        self._view.pos += 1
        if self._view.pos == self._view.maxpos + 1:
            cc = [x for x in self._view.selected]
            jr = ", ".join
            desc = "\n".join(
                [
                    f'ㅤ**Question:** *"{entry[0]}"*\nㅤ**Response:** {entry[4]}\nㅤ**Answer[s]:** {jr(entry[5])}\n'
                    for entry in self._view.selected
                ]
            )
            cor = [x[3] for x in cc].count(True)
            tot = len(self._view.selected)
            per = (cor / tot) * 100
            score = f"\n`{cor} / {tot} [{per}%]`"

            base_winnings = 5000
            mults = {"Easy": 0.75, "Medium": 1, "Hard": 1.25}
            perc = round(
                base_winnings
                * mults[self._view.dif]
                * ([x[3] for x in cc].count(True) / self._view.maxpos)
            )

            coin = CONSTANTS.Emojis().COIN_ID
            embed = fmte_i(
                interaction,
                t=f"Quiz Finished! You Earned `{perc:,}`{coin}!\nCategory: `{self._view.cat}`\nDifficulty: `{self._view.dif}`",
                d=f"**Results:**\n{desc}{score}",
            )

            db = BalanceDatabase(self.ctx)
            await db.addToBalance(self.ctx.author, perc)

            await interaction.response.edit_message(embed=embed, view=None)
        else:
            # print(self._view.pos, self.select.values)
            question = self._view.questions[self._view.pos - 1]
            embed = self._view.embed(interaction)
            view = MainQuizView(
                self._view.questions, self._view.cat, self._view.dif, self._view.ctx
            )
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
        super().__init__(
            style=discord.ButtonStyle.danger, label="Close", emoji="\N{CROSS MARK}"
        )

    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.message.delete()


class BalanceDatabase:
    def __init__(self, ctx: commands.Context):
        self.bot: commands.Bot = ctx.bot
        self.apg: asyncpg.Connection = ctx.bot.apg

    async def registerUser(self, user: discord.User) -> asyncpg.Record:
        command = """
            INSERT INTO users(userid)
            VALUES (
                $1
            )
            ON CONFLICT DO NOTHING
            RETURNING *
        """
        return await self.apg.fetchrow(command, user.id)

    async def addToBalance(self, user: discord.User, value: int) -> asyncpg.Record:
        try:
            await self.registerUser(user)
            command = """
                UPDATE users
                SET balance = balance + $1
                WHERE userid = $2
                RETURNING *
            """
            return await self.apg.fetchrow(command, value, user.id)
        except asyncpg.CheckViolationError:
            command = """
                UPDATE users
                SET balance = 0
                WHERE userid = $1
                RETURNING *
            """
            return await self.apg.fetchrow(command, value, user.id)

    async def getBalance(self, user: discord.User) -> int:
        await self.registerUser(user)
        command = """
            SELECT balance
            FROM users
            WHERE userid = $1
        """
        return (await self.apg.fetchrow(command, user.id))["balance"]

    async def delete(self, user: discord.User) -> None:
        command = """
            DELETE FROM users
            WHERE userid = $1
        """
        await self.apg.execute(command, user.id)

    async def leaderboard(self, members: List[discord.Member]) -> List[asyncpg.Record]:
        command = """
            SELECT * FROM users
            WHERE userid = $1
        """
        users: List[asyncpg.Record] = list()
        for member in members:
            value: asyncpg.Record = await self.apg.fetchrow(command, member.id)
            if value is None or value["balance"] <= 0:
                continue
            users.append(value)
        users.sort(key=lambda r: r["balance"], reverse=True)
        return users


async def setup(bot):
    await bot.add_cog(Currency(bot, True))
