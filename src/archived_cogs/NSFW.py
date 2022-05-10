import asyncio
import io
import time
from typing import List, Optional
import aiohttp
import bs4
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

import os
import math
import random
import shutil
from bs4 import BeautifulSoup
import requests
import wget

from _aux.embeds import fmte, fmte_i


class NSFW(commands.Cog):
    """
    For the horny ones. Do not use if you are not 18 years or older.
    """

    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot

    def ge(self):
        return "🔞"

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(querey="The keywords to search for.",
              ephemeral="Whether to publicly send the response or not. All images are sent in DMs.")
    async def rule34(self, ctx: commands.Context, querey: str, ephemeral: bool = False):
        """
        Gets images from [rule34.xxx](https://rule34.xxx]) and sends the first 10 images to you.
        """
        querey = querey.replace(" ", "+")
        res = await (await self.bot.session.get(
            f"https://rule34.xxx/index.php?page=post&s=list&tags=%s)" % querey
        )).text
        soup = BeautifulSoup(res, 'html.parser')

        tags = soup.select(
            "div[id=content] > div[id=post-list] > div[class=content] > div[class=image-list] > *")

        urls = []

        embed = fmte(
            ctx,
            t="Results found...",
            d="Sending to author."
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

        for tag in tags:
            soup = BeautifulSoup(str(tag), "html.parser")
            url = soup.select_one("span[class=thumb] > a > img")["src"]
            urls.append(url)

        for url in urls[:10]:
            embed = fmte(
                ctx,
                t="R34 Request For: `{}`".format(" ".join(querey)),
                d="[Source]({})".format(url)
            )
            embed.set_image(url=url)
            await ctx.author.send(embed=embed)

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(amount="The amount of images to send.",
              ephemeral="Whether to publicly show the response to the command. All images are sent in DMs.")
    async def neko(self, ctx: commands.Context, amount: Range[int, 1, 20] = 1, ephemeral: bool = False):
        """
        Gets an image response from [nekos.life](https://nekos.life) and sends it to you.
        """

        data = []

        for co in range(amount):
            res = await (await self.bot.session.get(
                f"https://nekos.life"
            )).text()
            soup = BeautifulSoup(res, 'html.parser')
            img = soup.find_all("img")
            data.append(img[0]["src"])

        embed = fmte(
            ctx,
            t="Fetched Images",
            d="Sending...",

        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

        for l in data:
            embed = fmte(ctx, )
            embed.set_image(url=l)
            await ctx.author.send(embed=embed)

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(amount="The amount of images to send.",
              ephemeral="Whether to public send the response or not. All images are sent in DMs.")
    async def nekolewd(self, ctx: commands.Context, amount: Range[int, 1, 20] = 1, ephemeral: bool = False):
        """
        Gets an image response from [nekos.life/lewd](https://nekos.life/lewd) and sends it to you.
        """
        mdir = os.getenv("NSFW_PATH") + "Nekos/"
        data = []

        for co in range(amount):
            data.append(
                discord.File(
                    mdir + random.choice(os.listdir(mdir)),
                    "Neko.jpg"
                )
            )

        embed = fmte(
            ctx,
            t="Fetched Images",
            d="Sending...",
        )

        await ctx.send(embed=embed, ephemeral=ephemeral)

        for l in data:
            embed = fmte(ctx, )
            await ctx.author.send(embed=embed, file=l)
            await asyncio.sleep(1)

    @commands.hybrid_command()
    # @commands.cooldown(1, 60 * 60 * 24, commands.BucketType.user)
    @commands.is_nsfw()
    @describe(code="The code to search for.",
              ephemeral="Whether to public send the response or not. All images are sent in DMs.")
    async def nhentai(self, ctx: commands.Context, code: int, ephemeral: bool = False):
        """
        Uses [nhentai.xxx](https://nhentai.xxx) to get all pages within a manga, and sends them to you.
        """
        inst = NHentaiView(ctx, self.bot, False, code)
        embed = inst.page_zero(ctx.interaction)
        view = inst
        await view.checkButtons()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(querey="The keywords to search for.",
              ephemeral="Whether to public send the response or not. All images are sent in DMs.")
    async def nhsearch(self, ctx: commands.Context, querey: str, ephemeral: bool = False):
        """
        Searches for manga on [nhentai.xxx](https://nhentai.xxx) and returns the top results.
        """
        querey = querey.replace(" ", "+")
        url = "https://nhentai.xxx/search/?q=%s" % querey
        res = await (await self.bot.session.get(url)).text()
        parse = BeautifulSoup(
            res, "html.parser"
        )
        codes = []
        images = []
        names = []

        embed = fmte(
            ctx,
            t="Fetched Images",
            d="Sending..."
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

        for i in parse.find_all("div")[3:-1]:
            try:
                if not parse.select_one("div > a"):
                    continue
                nparse = BeautifulSoup(str(i), "html.parser")
                codes.append(nparse.select_one("div > a")["href"][3:-1])
                images.append(nparse.select_one("div > a > img")["src"])
                names.append(nparse.select_one("div > a > div"))
            except BaseException:
                continue

        if not len(codes) == len(images) == len(names):
            embed = fmte(
                ctx,
                t="Something odd happened, results may be incorrect. If so, please try another search."
            )
        else:
            embed = fmte(
                ctx,
                t="{} results found, sending to author...".format(len(codes))
            )
        await ctx.send(embed=embed, ephemeral=ephemeral)
        for n in range(
                min(codes.__len__(), images.__len__(), names.__len__())):
            c = n + 1
            tot = min(codes.__len__(), images.__len__(), names.__len__())

            name = str(names[n])[21:-6][:235]
            code = str(codes[n])
            url = str(images[n])
            embed = fmte(
                ctx,
                t="{} / {}\n{} [{}]".format(
                    c,
                    tot,
                    name,
                    code
                )
            )
            embed.set_image(url=url)
            await ctx.author.send(embed=embed)


class NHentaiView(discord.ui.View):
    def __init__(
            self,
            ctx: commands.Context,
            bot: commands.Bot,
            ephemeral: bool,
            code: int,
            *,
            timeout: Optional[float] = 180):
        self.ctx = ctx
        self.bot = bot
        self.ephemeral = ephemeral
        # text = await (await self.bot.session.get("https://nhentai.xxx/%s/1" %
        # code)).text()
        text = requests.get("https://nhentai.xxx/g/%s/1" % code).text
        soup = bs4.BeautifulSoup(text, "html.parser")
        dataurl = soup.select(
            "body > div#page-container > section#image-container > a > img")[0]["src"]
        datacode = dataurl[26:-6]
        self.code = datacode
        self.baseurl = "https://cdn.nhentai.xxx/g/%s/" % datacode
        self.pos = 1

        super().__init__(timeout=timeout)

    @discord.ui.button(emoji="<:BArrow:971590903837913129>", custom_id="b")
    async def back(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos -= 1
        await self.checkButtons(button)

        embed = self.embed(inter)
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.red, custom_id="x")
    async def close(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.message.delete()

    @discord.ui.button(emoji="📜", custom_id="c")
    async def cust(self, inter: discord.Interaction, button: discord.ui.button):
        q = await self.ctx.send("Please send a new page number...", ephemeral=False)
        r = await self.bot.wait_for("message", check=lambda m: m.channel == self.ctx.channel and m.author == self.ctx.author and m.content.isdigit())
        self.pos = int(r.content)
        try:
            await q.delete()
        except BaseException:
            pass

        try:
            await q.delete()
        except BaseException:
            pass
        await self.checkButtons(button)
        embed = self.embed(inter)
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:FArrow:971591003893006377>", custom_id="f")
    async def next(self, inter: discord.Interaction, button: discord.ui.Button):
        self.pos += 1
        await self.checkButtons(button)

        embed = self.embed(inter)
        await inter.response.edit_message(embed=embed, view=self)

    def embed(self, inter: discord.Interaction):
        embed = fmte_i(
            inter,
            t="`{}`: Page `{}`".format(self.code, self.pos)
        )
        embed.set_image(url=self.baseurl + "%s.jpg" % self.pos)
        return embed

    def page_zero(self, interaction: discord.Interaction):
        self.pos = 1
        return self.embed(interaction)

    async def checkButtons(self, button: discord.Button = None):
        l = await self.bot.session.get(self.baseurl + "%s.jpg" % (self.pos - 1))
        n = await self.bot.session.get(self.baseurl + "%s.jpg" % (self.pos + 1))
        if l.status != 200:
            for b in self.children:
                if isinstance(b, discord.ui.Button):
                    if b.custom_id in ("b", "bb"):
                        b.disabled = True
        else:
            for b in self.children:
                if isinstance(b, discord.ui.Button):
                    if b.custom_id in ("b", "bb"):
                        b.disabled = False
        if n.status != 200:
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
    await bot.add_cog(NSFW(bot))
