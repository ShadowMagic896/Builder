import discord
from discord.ext import commands

import asyncio
import os
import pyautogui
import subprocess
import time

from _aux.embeds import fmte
class GUI(commands.Cog):
    def __init__(self, bot: discord.ext.commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group()
    async def gui(self, ctx):
        pass

    @gui.command()
    @commands.is_owner()
    async def goto(self, ctx: commands.Context, x: int, y: int):
        pyautogui.moveTo(x, y)
    
    @gui.command()
    async def ss(self, ctx: commands.Context, regionx:int = 0, regiony:int = 0, regionwidth:int = pyautogui.size()[0], regionheight:int = pyautogui.size()[1]):
        pyautogui.screenshot(region=(regionx, regiony, regionwidth, regionheight)).save("pyauto_resources/game_image.jpg")
        f = discord.File("pyauto_resources/game_image.jpg", filename = "Game_Image.jpg")
        await ctx.message.reply(file = f)

    @gui.command()   
    @commands.is_owner()           
    async def open(self, ctx: discord.ext.commands.Context, location: str = "C:\\Users\\ryano\\Downloads\\VisualBoyAdvance.exe"):
        os.startfile(location)
    
    @gui.command()
    @commands.is_owner()
    async def emu(self, ctx, game:str = "Pokemon\\FireRed", framerate: float = 1.0):
        rom_path = "R:\\mGBA\\mGBA.exe \"R:\\mGBA\\_games\\{}\\{}.gba\"".format(game, game[game.index("\\")+1:]) #FireRed.gba
        subprocess.Popen(rom_path)
        
        await asyncio.sleep(1.5) # Give time to open
        window = [w for w in pyautogui.getAllWindows() if w.title.startswith("mGBA")][0]

        window.maximize()
        for win in pyautogui.getAllWindows():
            if win != window:
                win.minimize()

        window.minimize()
        window.maximize()
        
        ctx.start_time = time.time()
        ms = await ctx.send("Creating emulation...")
        while True:
            embed = fmte(
                ctx=ctx,
                t="Playing: {}".format(game.replace("\\", ": ")),
                d="For: {} minutes".format(round((time.time() - ctx.start_time) / 60, 2))
            )
            pyautogui.screenshot(region=(212,45, 1706-212, 1038-45)).save("pyauto_resources/game_image.jpg")
            file = discord.File("pyauto_resources/game_image.jpg", filename = "Game_Image.jpg")
            view = VBA_View(ctx, ctx.bot, ms)
            try:
                await ms.edit(
                    embed = embed,
                    attachments = [file,],
                    view = view
                )
            except discord.errors.NotFound:
                break
            # await asyncio.sleep(float(framerate))
            await asyncio.sleep(2)

class VBA_View(discord.ui.View):
    def __init__(self, ctx, bot, msg = None):
        super().__init__(timeout = 900)
        self.ctx = ctx
        self.bot = bot
        self.res_msg = msg
    
    async def pong(interaction):
        """Tells discord to stfu bozo"""
        try:
            await interaction.response.send_message()
        except:
            pass
    
    @discord.ui.button(
        label = "L",
        style = discord.ButtonStyle.green,
        row = 0
    )
    async def leftTrigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        pyautogui.keyDown("l")
        await asyncio.sleep(1)
        pyautogui.keyUp("l")


    @discord.ui.button(
        label = "🔼",
        style = discord.ButtonStyle.blurple,
        row = 0
    )
    async def upArrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        
        pyautogui.keyDown("up")
        await asyncio.sleep(0.5)
        pyautogui.keyUp("up")


    @discord.ui.button(
        label = "R",
        style = discord.ButtonStyle.green,
        row = 0
    )
    async def rightTrigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        
        pyautogui.keyDown("r")
        await asyncio.sleep(1)
        pyautogui.keyUp("r")

    
    @discord.ui.button(
        label = "◀️",
        style = discord.ButtonStyle.blurple,
        row = 1
    )
    async def leftArrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)

        pyautogui.keyDown("left")
        await asyncio.sleep(0.5)
        pyautogui.keyUp("left")
    
    @discord.ui.button(
        label = " ",
        style = discord.ButtonStyle.grey,
        row = 1
    )
    async def blank(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
    
    @discord.ui.button(
        label = "▶️",
        style = discord.ButtonStyle.blurple,
        row = 1
    )
    async def rightArrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        
        pyautogui.keyDown("right")
        await asyncio.sleep(0.5)
        pyautogui.keyUp("right")


    
    @discord.ui.button(
        label = "B",
        style = discord.ButtonStyle.blurple,
        row = 2
    )
    async def BButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        
        pyautogui.keyDown("b")
        await asyncio.sleep(1)
        pyautogui.keyUp("b")
    

    
    @discord.ui.button(
        label = "🔽",
        style = discord.ButtonStyle.blurple,
        row = 2
    )
    async def downArrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        
        pyautogui.keyDown("down")
        await asyncio.sleep(0.5)
        pyautogui.keyUp("down")
    
    
    @discord.ui.button(
        label = "A",
        style = discord.ButtonStyle.blurple,
        row = 2
    )
    async def AButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        
        pyautogui.keyDown("a")
        await asyncio.sleep(1)
        pyautogui.keyUp("a")

    
    @discord.ui.button(
        label = "SEL",
        style = discord.ButtonStyle.blurple,
        row = 3
    )
    async def select(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        
        pyautogui.keyDown("enter")
        await asyncio.sleep(1)
        pyautogui.keyUp("enter")

    
    @discord.ui.button(
        label = "❌",
        style = discord.ButtonStyle.red,
        row = 3
    )
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)

        if self.res_msg: await self.res_msg.delete()

        pyautogui.hotkey("shiftleft", "f1")
        subprocess.Popen("taskkill /IM mGBA.exe")
        embed = fmte(
            ctx=self.ctx,
            t = "Emulator closed.",
            d = "Thanks for playing! I hope you saved your game."
        )
        try: await self.ctx.message.reply(embed=embed)
        except discord.errors.NotFound: await self.ctx.send(embed=embed)
    
    @discord.ui.button(
        label = "SRT",
        style = discord.ButtonStyle.blurple,
        row = 3
    )
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        await VBA_View.pong(interaction=interaction)
        
        pyautogui.keyDown("shiftright")
        await asyncio.sleep(1)
        pyautogui.keyUp("shiftright")


async def setup(bot):
    await bot.add_cog(GUI(bot))