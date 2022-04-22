from os import stat
from random import random
import discord
from discord.app_commands import Range
from discord.ext import commands

import asyncio
import random
import pyfiglet
from pyfiglet import Figlet
from typing import List

from _aux.embeds import fmte, gge
from _aux.userio import is_user

class Fun(commands.Cog):
    """
    If you wanna have a good time...
    """

    def __init__(self, bot) -> None:
        self.bot = bot
    
    def ge(self):
        return "⚽"

    @commands.hybrid_command(aliases = ["text"])
    async def font(self, ctx, font: str, *, text: str):
        """
        Translates your text into a new font!
        """
        try:
            t = Figlet(font).renderText(" ".join(text))
            embed = fmte(ctx, t = "Rendering Finished!")
            if len(t) > 1990:
                embed.set_footer(text = "Requested by {}\n[Tuncated because of size]".format(ctx.author))
            await ctx.message.reply("```{}```".format(t[:1990]), embed = embed)
                
        except pyfiglet.FontNotFound:
            raise commands.errors.BadArgument("Font not found.")
    
    @commands.hybrid_command(aliases = ["dice", "diceroll"])
    async def roll(self, ctx, sides: Range[int, 1, 20000] = 20, times: Range[int, 1, 200] = 1):
        """
        Rolls a dice a certain amount of times. If the dice fall off of the table, we reroll.
        """
        results = []
        for c in range(times):
            results.append(random.randrange(0 + 1, sides + 1))
        formatted = ""
        for c, r in enumerate(results):
            if times <= 25:
                formatted += "`Roll {}: {}`\n".format(("0" * (len(str(times)) - len(str(c+1)))) + str(c+1), r)
            else:
                formatted += "`{}`".format(r)
        embed = fmte(
            ctx,
            t = "Rolling `{}`-sided die `{}` time{}...".format(
                sides, times, "s" if times != 1 else ""
            ),
            d = formatted
        )
        await ctx.send(embed = embed)
    
    def getTTTEmbed(ctx, players, current):
        embed = fmte(
            ctx,
            t = "{} is playing with {}".format(players[0], players[1]),
            d = "{}, it's your turn!".format(current)
        )
        return embed
    
    def getRPSEmbed(ctx, players, current):
        embed = fmte(
            ctx,
            t = "{} is playing with {}".format(players[0], players[1]),
            d = "Please choose your weapons...".format(current)
        )
        return embed
    
    def check(ctx, r, u, ms):
        # I would do this in a lambda but it's so big
        return all([
            not u.bot, # User isn't a bot
            str(r.emoji) in ["✅", "❌"], 
            r.message == ms, # On the message I sent
            u == ctx.author if str(r.emoji) == "❌" else True, # If it's an X, it was the author
            u != ctx.author if str(r.emoji) == "✅" else True # If it's an check, it was the author
        ])

    @commands.hybrid_command(aliases = ["tictactoe", "naughtsandcrosses"])
    async def ttt(self, ctx, user: str = None):
        """
        Offers a game of TicTacToe to the user.
        If no user is given, it will let anyone join.
        User can be a name, name and discriminator, ID, or mention.
        """
        if user:
            _user = await is_user(ctx, user)
            if _user == ctx.author or _user.bot or not _user:
                raise commands.errors.MemberNotFound(user)

            user = _user

            embed = fmte(
                ctx = ctx,
                t = "Waiting for {} to respond...".format(user),
                d = "{}, please react below.".format(user)
            )
            ms: discord.Message = await ctx.send(embed=embed)
            await ms.add_reaction("✅")
            await ms.add_reaction("❌")
            
            r, u = await self.bot.wait_for("reaction_add", check = lambda r, u: u == user and str(r.emoji) in ["✅", "❌"] and r.message == ms, timeout = 30)
            if (r.emoji) == "✅":
                embed = Fun.getTTTEmbed(ctx, (ctx.author, user), ctx.author)
                await ms.edit(embed=embed, view = TTT_GameView(ctx, (ctx.author, user), ctx.author))
            else:
                embed = fmte(
                    ctx,
                    t = "{} declined the match.".format(user),
                    d = "Sorry! Please choose someone else."
                )
                await ms.edit(embed=embed)
            await ms.remove_reaction("✅", self.bot.user)
            await ms.remove_reaction("✅", user)
            await ms.remove_reaction("❌", self.bot.user)
            await ms.remove_reaction("❌", user)
        else:
            embed = fmte(
                ctx,
                t = "Waiting for anyone to respond...",
                d = "React to this message to play Tic Tac Toe with {}!".format(ctx.author)
            )
            ms = await ctx.send(embed=embed)
            await ms.add_reaction("✅")
            await ms.add_reaction("❌")
            r, u = await self.bot.wait_for("reaction_add", check = lambda r, u: Fun.check(ctx, r, u, ms), timeout = 30)
            # From here, I know that if it is a check mark, it was not the author and if it was an X, it was not the author thanks to the Check above
            if str(r.emoji) == "❌":
                embed = fmte(
                    ctx,
                    t = "{} has closed the game offering".format(ctx.author),
                    d = "Maybe ask them again?"
                )
                await ms.edit(embed=embed)
                await ms.remove_reaction("✅", self.bot.user)
                await ms.remove_reaction("❌", self.bot.user)
                await ms.remove_reaction("❌", ctx.author)
                return
            elif r.emoji == "✅":
                embed = Fun.getTTTEmbed(ctx, (ctx.author, u), ctx.author)
                await ms.edit(embed=embed, view = TTT_GameView(ctx, (ctx.author, u), ctx.author))
                await ms.remove_reaction("✅", self.bot.user)
                await ms.remove_reaction("✅", u)
                await ms.remove_reaction("❌", self.bot.user)
    
    @commands.hybrid_command(aliases = ["rps", "roshambo", "rochambeau"])
    async def rockpaperscissors(self, ctx, user: str = None):
        """
        Offers a game of Rock Paper Scissors / Rochambeau to the user.
        If no user is given, it will let anyone join.
        User can be a name, name and discriminator, ID, or mention.
        """
        if user:
            _user = await is_user(ctx, user)
            if _user == ctx.author or _user.bot or not _user:
                raise commands.errors.UserNotFound(user)
                
            user = _user

            embed = fmte(   
                ctx = ctx,
                t = "Waiting for {} to respond...".format(user),
                d = "{}, please react below.".format(user)
            )
            ms: discord.Message = await ctx.send(embed=embed)
            await ms.add_reaction("✅")
            await ms.add_reaction("❌")
            r, u = await self.bot.wait_for("reaction_add", check = lambda r, u: u == user and str(r.emoji) in ["✅", "❌"] and r.message == ms, timeout = 30)
            if (r.emoji) == "✅":
                embed = Fun.getRPSEmbed(ctx, (ctx.author, user), ctx.author)
                await ms.edit(embed=embed, view = RPS_View(ctx, ctx.author, user))
            else:
                embed = fmte(
                    ctx,
                    t = "{} declined the match.".format(user),
                    d = "Sorry! Please choose someone else."
                )
                await ms.edit(embed=embed)
            await ms.remove_reaction("✅", self.bot.user)
            await ms.remove_reaction("✅", user)
            await ms.remove_reaction("❌", self.bot.user)
            await ms.remove_reaction("❌", user)
        else:
            embed = fmte(
                ctx,
                t = "Waiting for anyone to respond...",
                d = "React to this message to play Rock Paper Scissors with {}!".format(ctx.author)
            )
            ms = await ctx.send(embed=embed)
            await ms.add_reaction("✅")
            await ms.add_reaction("❌")
            
            r, u = await self.bot.wait_for("reaction_add", check = lambda r, u: Fun.check(ctx, r, u, ms), timeout = 30)
            # From here, I know that if it is a check mark, it was not the author and if it was an X, it was not the author thanks to the Check above
            if str(r.emoji) == "❌":
                embed = fmte(
                    ctx,
                    t = "{} has closed the game offering".format(ctx.author),
                    d = "Maybe ask them again?"
                )
                await ms.edit(embed=embed)
                await ms.remove_reaction("✅", self.bot.user)
                await ms.remove_reaction("❌", self.bot.user)
                await ms.remove_reaction("❌", ctx.author)
                return
            elif r.emoji == "✅":
                embed = Fun.getRPSEmbed(ctx, (ctx.author, u), ctx.author)
                await ms.edit(embed=embed, view = RPS_View(ctx, ctx.author, user))
                await ms.remove_reaction("✅", self.bot.user)
                await ms.remove_reaction("✅", u)
                await ms.remove_reaction("❌", self.bot.user)
                return



class TTT_GameView(discord.ui.View):
    def __init__(self, ctx, players: List[discord.Member], current: discord.Member):
        super().__init__(timeout = 45)
        self.ctx = ctx
        self.bot = ctx.bot
        self.players = players
        self.current = current
        self.past = [[],[]]
    
    async def pong(interaction):
        try:
            await interaction.response.send_message()
        except:
            pass    
    
    # 0 is in progress
    # 1 is p1 won
    # 2 is p2 won
    # 3 is tie
    async def getGameState(view: discord.ui.View, interaction: discord.Interaction, button: discord.ui.Button, pasts = List[List[int],]):

        if button.label == "X":
            _id = int(interaction.data["custom_id"])
            pasts[0].append(_id)
        elif button.label == "O":
            _id = int(interaction.data["custom_id"])
            pasts[1].append(_id)
        
        winning_patterns = [
            # Rows
            [0,1,2,],
            [3,4,5,],
            [6,7,8,],

            # Columns
            [0,3,6,],
            [1,4,7,],
            [2,5,8,],

            # Diagonals
            [0,4,8,],
            [2,4,6,],
        ]  

        for p in winning_patterns:
            if "".join(map(str, p)) in "".join(map(str, sorted(pasts[0]))):
                return (pasts, 1)
            elif "".join(map(str, p)) in "".join(map(str, sorted(pasts[1]))):
                return (pasts, 2)
            elif all([c.disabled for c in view._children]):
                return (pasts, 3)
        return (pasts, 0)
        
        
        


    async def update_events(self, interaction: discord.Interaction, button: discord.ui.Button):
        await TTT_GameView.pong(interaction)

        if interaction.user != self.current:
            return
        
        self.current = self.players[1] if self.current == self.players[0] else self.players[0]

        button.label = "X" if interaction.user == self.players[0] else "O"

        button.style = discord.ButtonStyle.green if interaction.user == self.players[0] else discord.ButtonStyle.red

        button.disabled = True

        past, state = await TTT_GameView.getGameState(self, interaction, button, self.past)
        self.past = past

        if state == 0: # Still playing
            embed = fmte(
                ctx = self.ctx,
                t = "Playing game with {} and {}".format(self.players[0], self.players[1]),
                d = "{}, it's your turn!".format(self.current)
            )
            await interaction.message.edit(embed = embed, view = self)
        elif state in [1,2]:
            for b in self._children:
                b.disabled = True
            embed = fmte(
                ctx = self.ctx,
                t = "{} has won!".format(self.players[0] if state == 1 else self.players[1]),
                d = "Well played, both sides."
            )
            await interaction.message.edit(embed = embed, view = self)
        else:
            for b in self._children:
                b.disabled = True
            embed = fmte(
                ctx = self.ctx,
                t = "It's a tie!",
                d = "Well played, both sides."
            )
            await interaction.message.edit(embed = embed, view = self)

        
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 0, custom_id = "0" )
    async def b0(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 0, custom_id = "1"  )
    async def b1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 0, custom_id = "2"  )
    async def b2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 1, custom_id = "3"  )
    async def b3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 1, custom_id = "4"  )
    async def b4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 1, custom_id = "5"  )
    async def b5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 2, custom_id = "6"  )
    async def b6(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 2, custom_id = "7"  )
    async def b7(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)
    
    @discord.ui.button( style = discord.ButtonStyle.grey, label = " ", row = 2, custom_id = "8"  )
    async def b8(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_events(interaction, button)

    
class RPS_View(discord.ui.View):
    def __init__(self, ctx: commands.Context, p1, p2, choices = {}):
        super().__init__(timeout = 30)
        self.ctx = ctx
        self.bot = ctx.bot
        self.p1 = p1
        self.p2 = p2
        self.choices = choices

    def state(self, p1: discord.Member, p2: discord.Member, p1choice, p2choice) -> discord.Member | None:
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

    async def update_events(self, interaction: discord.Interaction, select: discord.ui.Select):
        await TTT_GameView.pong(interaction)
        if interaction.user not in [self.p1, self.p2] or interaction.user in list(self.choices.keys()):
            await self.ctx.send("something happened")
            return
        self.choices[interaction.user] = interaction.data["values"][0]
        users_decided = list(self.choices.keys())
        if self.p1 in users_decided and self.p2 in users_decided:
            gamestate = self.state(self.p1, self.p2, self.choices[self.p1], self.choices[self.p2])

            if gamestate:
                loser = self.p1 if self.p1 != gamestate else self.p2
                embed = fmte(
                    self.ctx,
                    t = "{} has won! {} beats {}.".format(gamestate.name, self.choices[gamestate], self.choices[loser]),
                    d = "Well guessed, both sides."
                )
                await interaction.message.edit(embed = embed, view = None)
            else:
                embed = fmte(
                    self.ctx,
                    t = "It's a tie! Both users guessed {}".format(self.choices[self.p1])
                )
                await interaction.message.edit(embed = embed, view = None)
        else:
            ready = self.p1 if self.p1 in users_decided else self.p2
            waiting_for = self.p1 if self.p1 not in users_decided else self.p2
            embed = fmte(
                self.ctx,
                t = "{} has made a decision.".format(ready.name),
                d = "Waiting for {}...".format(waiting_for.name)
            )
            await interaction.message.edit(embed = embed, view = RPS_View(self.ctx, self.p1, self.p2, self.choices))

    @discord.ui.select(
        placeholder = "Please choose an option...",
        options = [
            discord.SelectOption(label = "Rock", description = "Crushes scissors, but gets covered by paper."),
            discord.SelectOption(label = "Paper", description = "Covers rock, but gets cut by scissors."),
            discord.SelectOption(label = "Scissors", description = "Cuts paper, but gets crushed by rock."),
        ]
    )
    async def selector(self, interaction: discord.Interaction, select: discord.ui.Select):
        await self.update_events(interaction, select)

            
async def setup(bot):
    await bot.add_cog(Fun(bot))