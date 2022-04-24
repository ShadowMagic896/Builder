import discord
from discord.app_commands import describe, Range
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError

import os
import math
import random
import requests
from bs4 import BeautifulSoup

from _aux.embeds import fmte


class NSFW(commands.Cog):
    """
    For the horny ones. Do not use if you are not 18 years or older.
    """

    def __init__(self, bot) -> None:
        self.bot = bot

    def ge(self):
        return "🔞"

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(
        querey="The keywords to search for.",
        ephemeral="Whether to publicly send the response or not. All images are sent in DMs.")
    async def r34(self, ctx: commands.Context, querey: str, ephemeral: bool = False):
        """
        Gets images from [rule34.xxx](https://rule34.xxx]) and sends the first 10 images to you.
        """
        res = requests.get(
            f"https://rule34.xxx/index.php?page=post&s=list&tags={'+'.join(querey.split('' ''))}+"
        ).text
        soup = BeautifulSoup(res, 'html.parser')

        tags = soup.select(
            "div[id=content] > div[id=post-list] > div[class=content] > div[class=image-list] > *")
        
        urls = []

        embed = fmte(
            ctx,
            t="Results found...",
            d="Send to channel."
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
    @describe(
        amount="The amount of images to send.",
        ephemeral="Whether to public send the response or not. All images are sent in DMs."
    )
    async def neko(self, ctx: commands.Context, amount: Range[int, 1, 20] = 1, ephemeral: bool = False):
        """
        Gets an image response from [nekos.life](https://nekos.life) and sends it to you.
        """

        data = []

        for co in range(amount):
            res = requests.get(
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
    @describe(
        amount="The amount of images to send.",
        ephemeral="Whether to public send the response or not. All images are sent in DMs."
    )
    async def nekolewd(self, ctx: commands.Context, amount: Range[int, 1, 20] = 1, ephemeral: bool = False):
        """
        Gets an image response from [nekos.life/lewd](https://nekos.life/lewd) and sends it to you.
        """
        data = []

        for co in range(amount):
            data.append(
                discord.File(
                    "R:\\__TheStuff\\Content\\Nekos\\" +
                    random.choice(
                        os.listdir("R:\\__TheStuff\\Content\\Nekos")),
                    "Neko.jpg"))

        embed = fmte(
            ctx,
            t="Fetched Images",
            d="Sending...",
        )

        await ctx.send(embed=embed, ephemeral=ephemeral)

        for l in data:
            embed = fmte(ctx, )
            await ctx.author.send(embed=embed, file=l)

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(
        code="The code to search for.",
        ephemeral="Whether to public send the response or not. All images are sent in DMs."
    )
    async def nhentai(self, ctx: commands.Context, code: int, ephemeral: bool = False):
        """
        Uses [nhentai.xxx](https://nhentai.xxx) to get all pages within a manga, and sends them to you.
        """
        res = requests.get(f"https://nhentai.xxx/g/{code}").text
        soup = BeautifulSoup(res, "html.parser")

        data = [
            img["src"]
            for img in soup.find_all("img")
        ][4:]

        embed = fmte(
            ctx,
            t="Fetched Images",
            d="Sending..."
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

        for co, x in enumerate(data[::2]):
            embed = fmte(
                ctx,
                t=f"{co+1} / {math.ceil(data.__len__()/2)}: {code}",
            )
            embed.set_image(url=x)
            await ctx.author.send(embed=embed)

    @commands.hybrid_command()
    @commands.is_nsfw()
    @describe(
        querey="The keywords to search for.",
        ephemeral="Whether to public send the response or not. All images are sent in DMs."
    )
    async def nhsearch(self, ctx: commands.Context, querey: str, ephemeral: bool = False):
        """
        Searches for manga on [nhentai.xxx](https://nhentai.xxx) and returns the top results.
        """
        url = "https://nhentai.xxx/search/?q={}".format(
            '+'.join(querey.split(" ")))
        res = requests.get(url).text
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
