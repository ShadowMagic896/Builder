from stat import filemode
from turtle import pu
import discord
from discord.ext import commands

import pyfiglet
from pyfiglet import Figlet

from _aux.embeds import fmte
from typing import Literal, Tuple

import pyautogui
import pygetwindow
import sys, os
import asyncio
import subprocess

import time

class Fun(commands.Cog):
    """Commands that are designed to be fun to use!"""

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.hybrid_command(name="font")
    async def font(self, ctx, font: Literal[
            "0.1-d", "ascii___", "banner0.1-D", "charset_", "gothic", "hollywood", "linux", "lockergnome", "lexible_", 
            "platoon_", "mike", "mini", "mirror", "mnemonic",  "modern__", "morse", "moscow", "slant", "trek", 
            "wavy", "weird", "tomahawk", "usaflag", 
        ], *, text: str):
        """
        Turns your text into a new font!
        Usage: >>font <font> <*text>
        """
        try:
            t = Figlet(font).renderText(" ".join(text))
            embed = fmte(ctx, t = "Rendering Finished!")
            if len(t) > 1990:
                embed.set_footer(text = "Requested by {}\n[Tuncated because of size]".format(ctx.author))
            await ctx.message.reply("```{}```".format(t[:1990]), embed = embed)
                
        except pyfiglet.FontNotFound:
            embed = fmte(
                ctx,
                t = "Sorry, I can't find that font.",
                d = "Maybe try another one, or use `>>help font` for all fonts",
            )
            await ctx.message.reply(embed = embed)
    
    @commands.hybrid_group()
    @commands.is_owner()
    async def gui(self, ctx):
        pass

    @gui.command()
    async def goto(self, ctx: commands.Context, x: int, y: int):
        pyautogui.moveTo(x, y)
    
    @gui.command()
    async def ss(self, ctx: commands.Context, regionX:int = 0, regionY:int = 0, regionWidth:int = pyautogui.size()[0], regionHeight:int = pyautogui.size()[1]):
        pyautogui.screenshot(region=(regionX, regionY, regionWidth, regionHeight)).save("pyauto_resources/game_image.jpg")
        f = discord.File("pyauto_resources/game_image.jpg", filename = "Game_Image.jpg")
        await ctx.message.reply(file = f)

    @gui.command()              
    async def open(self, ctx: discord.ext.commands.Context, file_location: str = "C:\\Users\\ryano\\Downloads\\VisualBoyAdvance.exe"):
        os.startfile(file_location)
    
    @gui.command()
    async def run_vba(self, ctx, framerate: float = 1.0):
        ms = await ctx.send("Loading emulator...")
        os.startfile("C:\\Users\\ryano\\Downloads\\VisualBoyAdvance.exe")
        
        while "VisualBoyAdvance" not in pyautogui.getAllTitles():
            continue
        window: pygetwindow.Win32Window = pyautogui.getWindowsWithTitle("VisualBoyAdvance")[0]
        window.maximize()
        for win in pyautogui.getAllWindows():
            if win.title != "VisualBoyAdvance":
                win.minimize()

        pyautogui.click(15, 30) # "File"
        await asyncio.sleep(0.1)
        pyautogui.click(15, 60) # "Open"
        await asyncio.sleep(0.1)
        pyautogui.click(800, 450, clicks = 2, interval=0.05) # Current ROM
        await asyncio.sleep(0.1)
        pyautogui.click(15, 30) # "File"
        await asyncio.sleep(0.1)
        pyautogui.click(15, 100) # "Load"
        await asyncio.sleep(0.1)
        pyautogui.click(800, 425, clicks = 2, interval=0.05) # Saves folder
        await asyncio.sleep(0.1)
        pyautogui.click(800, 425, clicks = 2, interval=0.05) # Save file
        await asyncio.sleep(0.1)

        window.minimize()
        window.maximize()
        
        ctx.start_time = time.time()

        embed = fmte(
            ctx=ctx,
            t="Playing: Pokemon: Fire Red",
            d="For: {} minutes".format((time.time() - ctx.start_time) / 60)
        )
        pyautogui.screenshot().save("pyauto_resources/game_image.jpg")
        file = discord.File("pyauto_resources/game_image.jpg", filename = "Game_Image.jpg")
        ms = await ctx.message.reply(embed=embed, file=file, view = VBA_View(ctx, ctx.bot, ms))

        while True:
            embed = fmte(
                ctx=ctx,
                t="Playing: Pokemon: Fire Red",
                d="For: {} minutes".format((time.time() - ctx.start_time) / 60)
            )
            pyautogui.screenshot().save("pyauto_resources/game_image.jpg")
            file = discord.File("pyauto_resources/game_image.jpg", filename = "Game_Image.jpg")
            view = VBA_View(ctx, ctx.bot,ms)
            try:
                await ms.edit(
                    embed = embed,
                    attachments = [file,],
                    view = view
                )
            except discord.errors.NotFound:
                await ctx.send("Emulator closed by user.")
                break
            await asyncio.sleep(float(framerate))


class VBA_View(discord.ui.View):
    def __init__(self, ctx, bot, msg):
        super().__init__()
        self.ctx = ctx
        self.bot = bot
        self.res_msg = msg
    
    @discord.ui.button(
        label = "L",
        style = discord.ButtonStyle.green,
        row = 0
    )
    async def leftTrigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        
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
        
        pyautogui.keyDown("up")
        await asyncio.sleep(1)
        pyautogui.keyUp("up")

    @discord.ui.button(
        label = "R",
        style = discord.ButtonStyle.green,
        row = 0
    )
    async def rightTrigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        
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
        
        pyautogui.keyDown("left")
        await asyncio.sleep(1)
        pyautogui.keyUp("left")
    
    @discord.ui.button(
        label = " ",
        style = discord.ButtonStyle.grey,
        row = 1
    )
    async def blank(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
    
    @discord.ui.button(
        label = "▶️",
        style = discord.ButtonStyle.blurple,
        row = 1
    )
    async def rightArrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        
        pyautogui.keyDown("right")
        await asyncio.sleep(1)
        pyautogui.keyUp("right")
    
    @discord.ui.button(
        label = "A",
        style = discord.ButtonStyle.blurple,
        row = 2
    )
    async def AButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        
        pyautogui.keyDown("a")
        await asyncio.sleep(1)
        pyautogui.keyUp("a")
    
    @discord.ui.button(
        label = "🔽",
        style = discord.ButtonStyle.blurple,
        row = 2
    )
    async def downArrow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        
        pyautogui.keyDown("down")
        await asyncio.sleep(1)
        pyautogui.keyUp("down")
    
    @discord.ui.button(
        label = "B",
        style = discord.ButtonStyle.blurple,
        row = 2
    )
    async def BButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        
        pyautogui.keyDown("b")
        await asyncio.sleep(1)
        pyautogui.keyUp("b")
    
    @discord.ui.button(
        label = "SEL",
        style = discord.ButtonStyle.blurple,
        row = 3
    )
    async def select(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        
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
        await self.res_msg.delete()
        subprocess.Popen("taskkill /IM VisualBoyAdvance.exe")
    
    @discord.ui.button(
        label = "SRT",
        style = discord.ButtonStyle.blurple,
        row = 3
    )
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author != interaction.user:
            return
        
        pyautogui.keyDown("shiftright")
        await asyncio.sleep(1)
        pyautogui.keyUp("shiftright")
    
    
    

            
async def setup(bot):
    await bot.add_cog(Fun(bot))