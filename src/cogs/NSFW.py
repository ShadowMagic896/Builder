import asyncio
import io
import time
from typing import List
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
import wget

from _aux.embeds import fmte


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
        res = self.bot.session.get(
            f"https://rule34.xxx/index.php?page=post&s=list&tags=%s)" % querey
        ).text
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
            res = self.bot.session.get(
                f"https://nekos.life"
            ).text
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
    @commands.cooldown(1, 60*60*24, commands.BucketType.user)
    @commands.is_nsfw()
    @describe(code="The code to search for.",
              ephemeral="Whether to public send the response or not. All images are sent in DMs.")
    async def nhentai(self, ctx: commands.Context, code: int, ephemeral: bool = False):
        """
        Uses [nhentai.xxx](https://nhentai.xxx) to get all pages within a manga, and sends them to you.
        """
        file_chunk_size = 10
        await ctx.interaction.response.defer(thinking=True)
        baseurl = "nhentai.xxx/g/%s/" % code

        
        embed = fmte(
            ctx,
            t = "Downloading Next Batch..."
        )
        m = await ctx.send(embed=embed)
        
        files: List[discord.File] = []
        page = -1
        batch = 0
        start_t = time.time()
        batch_t = time.time()
        file_t = time.time()
        while True:
            page += 1
            soup = bs4.BeautifulSoup(await (await self.bot.session.get("https://%s%s" % (baseurl, page+1))).text(), "html.parser")
            try:
                dataurl = soup.select("body > div#page-container > section#image-container > a > img")[0]["src"]
            except IndexError:
                await ctx.send(files=files)
                files.clear()
                return
            res = await self.bot.session.get(dataurl)
            b: io.BytesIO = io.BytesIO(await res.read())
            b.seek(0)
            files.append(discord.File(b, filename="%s_%s.jpg" % (code, page+1)))
            if len(files) % file_chunk_size == 0:
                # await m.remove_attachments(embed)
                embed = fmte(
                    ctx,
                    t = "Batch #%s Done" % (batch + 1),
                    d = "File Time: `{}s`\nBatch Time: `{}s`\nTotal Time: `{}s`".format(
                        round(t - file_t), round(t - batch_t), round(t - start_t)
                    )
                )
                m = await ctx.send(embed=embed, files=files)
                files.clear()
                batch_t = time.time()
                batch += 1
                continue
            else:
                t = time.time()
                embed = fmte(
                    ctx,
                    t = "Batch #%s File #%s Done" % (batch + 1, (page + 1) % file_chunk_size),
                    d = "File Time: `{}s`\nBatch Time: `{}s`\nTotal Time: `{}s`".format(
                        round(t - file_t), round(t - batch_t), round(t - start_t)
                    )
                )
                await m.edit(embed=embed)
                file_t = time.time()
                continue

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


async def setup(bot):
    await bot.add_cog(NSFW(bot))
