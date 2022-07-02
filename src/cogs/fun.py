import discord
import pyfiglet
import random
from discord.app_commands import Range, describe
from discord.ext import commands
from pyfiglet import Figlet
from random import random
from typing import List

from ..utils.bot_types import Builder, BuilderContext
from ..utils.embeds import Desc, format
from ..utils.subclass import BaseCog


class Fun(BaseCog):
    """
    If you wanna have a good time...
    """

    def __init__(self, bot: Builder) -> None:
        self.bot = bot
        self.emoji_check = "\N{WHITE HEAVY CHECK MARK}"
        self.emoji_cross = "\N{CROSS MARK}"

    def ge(self):
        return "\N{SOCCER BALL}"

    @commands.hybrid_command()
    @describe(
        font="The font to translate to. See http://www.figlet.org/fontdb.cgi for fonts.",
        text="The text to translate.",
    )
    async def font(
        self,
        ctx: BuilderContext,
        font: str,
        text: str,
    ):
        """
        Translates your text into a new font!
        """
        try:
            t = Figlet(font).renderText(text)
            embed = await format(ctx, title="Rendering Finished!")
            if len(t) > 1990:
                embed.set_footer(
                    text="Requested by {}\n[Tuncated because of size]".format(
                        ctx.author
                    )
                )
            await ctx.send("```{}```".format(t[:1990]), embed=embed)

        except pyfiglet.FontNotFound:
            raise commands.errors.BadArgument("Font not found.")

    @font.autocomplete("font")
    async def font_autocomplete(self, interaction: discord.Interaction, current: str):
        return sorted(
            [
                discord.app_commands.Choice(name=c, value=c)
                for c in Figlet().getFonts()
                if c.lower() in current.lower() or current.lower() in c.lower()
            ][:25],
            key=lambda c: c.name,
        )

    @commands.hybrid_command()
    @describe(
        sides="The amount of sides for the dice.",
        times="How many times to roll the dice.",
    )
    async def roll(
        self,
        ctx,
        sides: Range[int, 1, 20000] = 20,
        times: Range[int, 1, 200] = 1,
    ):
        """
        Rolls a dice a certain amount of times.
        """
        results = []
        for c in range(times):
            results.append(random.randrange(0 + 1, sides + 1))
        formatted = ""
        for c, r in enumerate(results):
            if times <= 25:
                formatted += "`Roll {}: {}`\n".format(
                    ("0" * (len(str(times)) - len(str(c + 1)))) + str(c + 1), r
                )
            else:
                formatted += "`{}`".format(r)
        embed = await format(
            ctx,
            title="Rolling `{}`-sided die `{}` time{}...".format(
                sides, times, "s" if times != 1 else ""
            ),
            desc=formatted,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @describe(user=Desc.user)
    async def tictactoe(self, ctx, user: discord.Member = None):
        """
        Offers a game of TicTacToe to the user.
        """
        if user:
            if user == ctx.author or user.bot or not user:
                raise commands.errors.BadArgument(user)

            embed = await format(
                ctx=ctx,
                title="Waiting for {} to respond...".format(user),
                desc="{}, please react below.".format(user),
            )

            ms: discord.Message = await ctx.send(embed=embed)
            await ms.add_reaction(self.emoji_check)
            await ms.add_reaction(self.emoji_cross)

            r, u = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: u == user
                and str(r.emoji) in [self.emoji_check, self.emoji_cross]
                and r.message == ms,
                timeout=30,
            )
            if (r.emoji) == self.emoji_check:
                embed = await Fun.getTTTEmbed(ctx, (ctx.author, user), ctx.author)
                await ms.edit(
                    embed=embed, view=TTT_GameView(ctx, (ctx.author, user), ctx.author)
                )
            else:
                embed = await format(
                    ctx,
                    title="{} declined the match.".format(user),
                    desc="Sorry! Please choose someone else.",
                )
                await ms.edit(embed=embed)
            await ms.clear_reactions()
        else:
            embed = await format(
                ctx,
                title="Waiting for anyone to respond...",
                desc="React to this message to play Tic Tac Toe with {}!".format(
                    ctx.author
                ),
            )
            ms = await ctx.send(embed=embed)
            await ms.add_reaction(self.emoji_check)
            await ms.add_reaction(self.emoji_cross)
            r, u = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: Fun(self.bot).check(ctx, r, u, ms),
                timeout=30,
            )

            if str(r.emoji) == self.emoji_cross:
                embed = await format(
                    ctx,
                    title="{} has closed the game offering".format(ctx.author),
                    desc="Maybe ask them again?",
                )
                await ms.edit(embed=embed)
                await ms.clear_reactions()
                return
            elif r.emoji == self.emoji_check:
                embed = await Fun.getTTTEmbed(ctx, (ctx.author, u), ctx.author)
                await ms.edit(
                    embed=embed, view=TTT_GameView(ctx, (ctx.author, u), ctx.author)
                )
                await ms.clear_reactions()

    @commands.hybrid_command(aliases=["rps", "roshambo", "rochambeau"])
    @describe(user=Desc.user)
    async def rockpaperscissors(self, ctx, user: discord.Member = None):
        """
        Offers a game of Rock Paper Scissors / Rochambeau to the user.
        If no user is given, it will let anyone join.
        User can be a name, name and discriminator, ID, or mention.
        """
        if user:
            if user == ctx.author or user.bot or not user:
                raise commands.errors.BadArgument(user)

            embed = await format(
                ctx=ctx,
                title="Waiting for {} to respond...".format(user),
                desc="{}, please react below.".format(user),
            )

            ms: discord.Message = await ctx.send(embed=embed)
            await ms.add_reaction(self.emoji_check)
            await ms.add_reaction(self.emoji_cross)
            r, u = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: u == user
                and str(r.emoji) in [self.emoji_check, self.emoji_cross]
                and r.message == ms,
                timeout=30,
            )
            if (r.emoji) == self.emoji_check:
                embed = await Fun.getRPSEmbed(ctx, (ctx.author, user), ctx.author)
                await ms.edit(embed=embed, view=RPS_View(ctx, ctx.author, user))
            else:
                embed = await format(
                    ctx,
                    title="{} declined the match.".format(user),
                    desc="Sorry! Please choose someone else.",
                )
                await ms.edit(embed=embed)
            await ms.clear_reactions()
        else:
            embed = await format(
                ctx,
                title="Waiting for anyone to respond...",
                desc="React to this message to play Rock Paper Scissors with {}!".format(
                    ctx.author
                ),
            )
            ms = await ctx.send(embed=embed)
            await ms.add_reaction(self.emoji_check)
            await ms.add_reaction(self.emoji_cross)

            r, u = await self.bot.wait_for(
                "reaction_add",
                check=lambda r, u: Fun(self.bot).check(ctx, r, u, ms),
                timeout=30,
            )
            # From here, I know that if it is a check mark, it was not the
            # author and if it was an X, it was not the author thanks to the
            # Check above
            if str(r.emoji) == self.emoji_cross:
                embed = await format(
                    ctx,
                    title="{} has closed the game offering".format(ctx.author),
                    desc="Maybe ask them again?",
                )
                await ms.edit(embed=embed)
                await ms.clear_reactions()
                return
            elif r.emoji == self.emoji_check:
                embed = await Fun.getRPSEmbed(ctx, (ctx.author, u), ctx.author)
                await ms.edit(embed=embed, view=RPS_View(ctx, ctx.author, user))
                await ms.clear_reactions()
                return

    async def getTTTEmbed(ctx, players, current):
        embed = await format(
            ctx,
            title="{} is playing with {}".format(players[0], players[1]),
            desc="{}, it's your turn!".format(current),
        )
        return embed

    async def getRPSEmbed(ctx, players, current):
        embed = await format(
            ctx,
            title="{} is playing with {}".format(players[0], players[1]),
            desc="Please choose your weapons...".format(current),
        )
        return embed

    def check(self, ctx, r, u, ms):
        return all(
            [
                not u.bot,
                str(r.emoji) in [self.emoji_check, self.emoji_cross],
                r.message == ms,
                u == ctx.author if str(r.emoji) == self.emoji_cross else True,
                u != ctx.author if str(r.emoji) == self.emoji_check else True,
            ]
        )


class TTT_GameView(discord.ui.View):
    def __init__(self, ctx, players: List[discord.Member], current: discord.Member):
        super().__init__(timeout=45)
        self.ctx = ctx
        self.bot = ctx.bot
        self.players = players
        self.current = current
        self.past = [[], []]

    async def pong(interaction):
        try:
            await interaction.response.send_message()
        except BaseException:
            pass

    # 0 is in progress
    # 1 is p1 won
    # 2 is p2 won
    # 3 is tie
    async def getGameState(
        view: discord.ui.View,
        interaction: discord.Interaction,
        button: discord.ui.Button,
        pasts=List[
            List[int],
        ],
    ):

        if button.label == "X":
            _id = int(interaction.data["custom_id"])
            pasts[0].append(_id)
        elif button.label == "O":
            _id = int(interaction.data["custom_id"])
            pasts[1].append(_id)

        winning_patterns = [
            # Rows
            [
                0,
                1,
                2,
            ],
            [
                3,
                4,
                5,
            ],
            [
                6,
                7,
                8,
            ],
            # Columns
            [
                0,
                3,
                6,
            ],
            [
                1,
                4,
                7,
            ],
            [
                2,
                5,
                8,
            ],
            # Diagonals
            [
                0,
                4,
                8,
            ],
            [
                2,
                4,
                6,
            ],
        ]

        for p in winning_patterns:
            if "".join(map(str, p)) in "".join(map(str, sorted(pasts[0]))):
                return (pasts, 1)
            elif "".join(map(str, p)) in "".join(map(str, sorted(pasts[1]))):
                return (pasts, 2)
            elif all([c.disabled for c in view._children]):
                return (pasts, 3)
        return (pasts, 0)

    async def update_events(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await TTT_GameView.pong(interaction)

        if interaction.user != self.current:
            return

        self.current = (
            self.players[1] if self.current == self.players[0] else self.players[0]
        )

        button.label = "X" if interaction.user == self.players[0] else "O"

        button.style = (
            discord.ButtonStyle.green
            if interaction.user == self.players[0]
            else discord.ButtonStyle.red
        )

        button.disabled = True

        past, state = await TTT_GameView.getGameState(
            self, interaction, button, self.past
        )
        self.past = past

        if state == 0:  # Still playing
            embed = await format(
                ctx=self.ctx,
                title="Playing game with {} and {}".format(
                    self.players[0], self.players[1]
                ),
                desc="{}, it's your turn!".format(self.current),
            )
            await interaction.message.edit(embed=embed, view=self)
        elif state in [1, 2]:
            for b in self._children:
                b.disabled = True
            embed = await format(
                ctx=self.ctx,
                title="{} has won!".format(
                    self.players[0] if state == 1 else self.players[1]
                ),
                desc="Well played, both sides.",
            )
            await interaction.message.edit(embed=embed, view=self)
        else:
            for b in self._children:
                b.disabled = True
            embed = await format(
                ctx=self.ctx, title="It's a tie!", desc="Well played, both sides."
            )
            await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=0, custom_id="0")
    async def b0(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=0, custom_id="1")
    async def b1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=0, custom_id="2")
    async def b2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=1, custom_id="3")
    async def b3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=1, custom_id="4")
    async def b4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=1, custom_id="5")
    async def b5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=2, custom_id="6")
    async def b6(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=2, custom_id="7")
    async def b7(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    @discord.ui.button(style=discord.ButtonStyle.grey, label=" ", row=2, custom_id="8")
    async def b8(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)


class RPS_View(discord.ui.View):
    def __init__(self, ctx: BuilderContext, p1, p2, choices={}):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.bot = ctx.bot
        self.p1 = p1
        self.p2 = p2
        self.choices = choices

    def state(self, p1: discord.Member, p2: discord.Member, p1choice, p2choice):
        if p1choice == p2choice:
            return None
        if p1choice == "Rock":
            if p2choice == "Paper":
                return p2
            else:
                return p1
        if p1choice == "Paper":
            if p2choice == "Scissors":
                return p2
            else:
                return p1
        if p1choice == "Scissors":
            if p2choice == "Rock":
                return p2
            else:
                return p1

    async def update_events(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await TTT_GameView.pong(interaction)
        if interaction.user not in [self.p1, self.p2] or interaction.user in list(
            self.choices.keys()
        ):
            await self.ctx.send("something happened")
            return
        self.choices[interaction.user] = interaction.data["values"][0]
        users_decided = list(self.choices.keys())
        if self.p1 in users_decided and self.p2 in users_decided:
            gamestate = self.state(
                self.p1, self.p2, self.choices[self.p1], self.choices[self.p2]
            )

            if gamestate:
                loser = self.p1 if self.p1 != gamestate else self.p2
                embed = await format(
                    self.ctx,
                    title="{} has won! {} beats {}.".format(
                        gamestate.name, self.choices[gamestate], self.choices[loser]
                    ),
                    desc="Well guessed, both sides.",
                )
                await interaction.message.edit(embed=embed, view=None)
            else:
                embed = await format(
                    self.ctx,
                    title="It's a tie! Both users guessed {}".format(
                        self.choices[self.p1]
                    ),
                )
                await interaction.message.edit(embed=embed, view=None)
        else:
            ready = self.p1 if self.p1 in users_decided else self.p2
            waiting_for = self.p1 if self.p1 not in users_decided else self.p2
            embed = await format(
                self.ctx,
                title="{} has made a decision.".format(ready.name),
                desc="Waiting for {}...".format(waiting_for.name),
            )
            await interaction.message.edit(
                embed=embed, view=RPS_View(self.ctx, self.p1, self.p2, self.choices)
            )

    @discord.ui.select(
        placeholder="Please choose an option...",
        options=[
            discord.SelectOption(
                label="Rock", description="Crushes scissors, but gets covered by paper."
            ),
            discord.SelectOption(
                label="Paper", description="Covers rock, but gets cut by scissors."
            ),
            discord.SelectOption(
                label="Scissors", description="Cuts paper, but gets crushed by rock."
            ),
        ],
    )
    async def selector(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        await self.update_events(interaction, select)


async def setup(bot):
    await bot.add_cog(Fun(bot))
