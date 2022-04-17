import discord
from discord.ext import commands

import asyncio

from typing import List

from _aux.embeds import fmte

class TicTacToe(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot
    
    def getGameEmbed(ctx, players, current):
        embed = fmte(
            ctx,
            t = "{} is playing with {}".format(players[0], players[1]),
            d = "{}, it's your turn!".format(current)
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
    async def ttt(self, ctx, user: discord.Member = None):
        if user:
            if user == ctx.author or user.bot:
                embed = fmte(
                    ctx,
                    t = "Sorry, that's an invalid member.",
                    d = "Please try somebody else.",
                    c = discord.Color.yellow()
                )
                await ctx.send(embed=embed)
                return

            embed = fmte(
                ctx = ctx,
                t = "Waiting for {} to respond...".format(user),
                d = "{}, please react below.".format(user)
            )
            ms: discord.Message = await ctx.send(embed=embed)
            await ms.add_reaction("✅")
            await ms.add_reaction("❌")
            try:
                r, u = await self.bot.wait_for("reaction_add", check = lambda r, u: u == user and str(r.emoji) in ["✅", "❌"] and r.message == ms, timeout = 30)
                if (r.emoji) == "✅":
                    embed = TicTacToe.getGameEmbed(ctx, (ctx.author, user), ctx.author)
                    await ms.edit(embed=embed, view = TTT_GameView(ctx, ctx.bot, (ctx.author, user), ctx.author))
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
            except asyncio.TimeoutError:
                embed = fmte(
                    ctx,
                    t = "Sorry, {} didn't respond in time.".format(user),
                )
                await ms.edit(embed=embed)
                await ms.remove_reaction("✅", self.bot.user)
                await ms.remove_reaction("❌", self.bot.user)
                return
        else:
            embed = fmte(
                ctx,
                t = "Waiting for anyone to respond...",
                d = "React to this message to play Tic Tac Toe with {}!".format(ctx.author)
            )
            ms = await ctx.send(embed=embed)
            await ms.add_reaction("✅")
            await ms.add_reaction("❌")
            try:
                r, u = await self.bot.wait_for("reaction_add", check = lambda r, u: TicTacToe.check(ctx, r, u, ms), timeout = 30)
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
                    embed = TicTacToe.getGameEmbed(ctx, (ctx.author, u), ctx.author)
                    await ms.edit(embed=embed, view = TTT_GameView(ctx, self.bot, (ctx.author, u), ctx.author))
                    await ms.remove_reaction("✅", self.bot.user)
                    await ms.remove_reaction("✅", u)
                    await ms.remove_reaction("❌", self.bot.user)
                    return

            except asyncio.TimeoutError:
                embed = fmte(
                    ctx,
                    t = "Sorry, nobody responded in time.",
                    d = "Please remember that someone has to react to the message with `✅` within 30 seconds."
                )
                await ms.edit(embed=embed)
                await ms.remove_reaction("✅", self.bot.user)



class TTT_GameView(discord.ui.View):
    def __init__(self, ctx, bot, players: List[discord.Member], current: discord.Member):
        super().__init__(timeout = 45)
        self.ctx = ctx
        self.bot = bot
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

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))