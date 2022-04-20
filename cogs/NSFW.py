from re import T
from typing import ContextManager
import discord
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError  

import os
import asyncio
import math
import random
import requests
from bs4 import BeautifulSoup

from _aux.embeds import fmte

class NSFW(commands.Cog):
    @commands.hybrid_group()
    async def nsfw(self, ctx: commands.Context):
        """
        NSFW (Not Safe For Work) commands. If you are under 18, do not use these commands.
        Neither this bot nor its owners or developers are responsible for any content returned.
        """
        embed = fmte(
            ctx,
            t = "**Command Group `{}`**".format(ctx.invoked_parents[0]),
            d = "**All Commands:**\n{}".format("".join(["ㅤㅤ`>>{} {} {}`\nㅤㅤ*{}*\n\n".format(
                ctx.invoked_parents[0], 
                c.name, 
                c.signature, 
                c.short_doc
            ) for c in getattr(self, ctx.invoked_parents[0]).commands]))
        )
        await ctx.send(embed = embed)
        
    @nsfw.command(aliases=["rule34"])
    async def r34(self, ctx: commands.Context, *, query: str):
        """
        Gets images from [rule34.xxx](https://rule34.xxx]) and sends the first 10 images to you.
        """
        query = query.split(" ")
        res = requests.get(
            f"https://rule34.xxx/index.php?page=post&s=list&tags={'+'.join(query)}+"
        ).text
        soup = BeautifulSoup(res, 'html.parser')

        tags = soup.select("div[id=content] > div[id=post-list] > div[class=content] > div[class=image-list] > *")

        urls = []

        for tag in tags:
            soup = BeautifulSoup(str(tag), "html.parser")
            url = soup.select_one("span[class=thumb] > a > img")["src"]
            urls.append(url)
        
        for url in urls[:10]:
            embed = fmte(
                ctx,
                t = "R34 Request For: `{}`".format(" ".join(query)),
                d = "[Source]({})".format(url)
            )
            embed.set_image(url = url)
            await ctx.author.send(embed=embed)


    @nsfw.command()
    @commands.is_nsfw()
    async def neko(self, ctx: commands.Context, amount: int = 1):
        """
        Gets an image response from [nekos.life](https://nekos.life) and sends it to you.
        """
        if 1 < amount > 10:
            raise CommandInvokeError("Invalid amount")

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
            t="Image(s) returned!",
            d="This bot is not responsible for any image returned.",

        )
        await ctx.send(embed=embed)

        for l in data:
            embed = fmte( ctx, )
            embed.set_image(url=l)
            await ctx.send(embed=embed)

    @nsfw.command(aliases=["nekol"])
    @commands.is_nsfw()
    async def nekolewd(self, ctx: commands.Context, amount: int = 1):
        """
        Gets an image response from [nekos.life/lewd](https://nekos.life/lewd) and sends it to you.
        """
        if 1 < amount > 10:
            raise CommandInvokeError("Invalid amount")
        data = []

        for co in range(amount):
            data.append(discord.File("R:\\__TheStuff\\Content\\Nekos\\" + random.choice(os.listdir("R:\\__TheStuff\\Content\\Nekos")), "Neko.jpg"))

        embed = fmte(
            ctx,
            t = "Image(s) returned!",
            d = "This bot is not responsible for any image returned.",
        )

        await ctx.author.send(embed=embed)

        for l in data:
            embed = fmte( ctx, )
            await ctx.author.send(embed=embed, file = l)

    @nsfw.command(aliases=["nhg", "nh"])
    @commands.is_nsfw()
    async def nhentai(self, ctx: commands.Context, code: int):
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
            t = f"Check your DMs, {ctx.author}",
        )
        await ctx.reply(embed=embed)
        embed = fmte(
            ctx,
            t = "Image(s) returned!",
            d = "This bot is not responsible for any image returned.",
        )
        await ctx.author.send(embed=embed)
        for co, x in enumerate(data[::2]):
            embed = fmte(
                ctx,
                t=f"{co+1} / {math.ceil(data.__len__()/2)}: {code}",
            )
            embed.set_image(url=x)
            await ctx.author.send(embed=embed)

    @nsfw.command(aliases=["nhs", "nhentaisearch"])
    @commands.is_nsfw()
    async def nhsearch(self, ctx: commands.Context, *, query: str):
        """
        Searches for manga on [nhentai.xxx](https://nhentai.xxx) and returns the top results.
        """
        url = "https://nhentai.xxx/search/?q={}".format('+'.join(query.split(" ")))
        res = requests.get(url).text
        parse = BeautifulSoup(
            res, "html.parser"
        )
        codes = []
        images = []
        names = []
        
        for i in parse.find_all("div")[3:-1]:
            try:
                if not parse.select_one("div > a"):
                    continue
                nparse = BeautifulSoup(str(i), "html.parser")
                codes.append(nparse.select_one("div > a")["href"][3:-1])
                images.append(nparse.select_one("div > a > img")["src"])
                names.append(nparse.select_one("div > a > div"))
            except:
                continue
        
        if not len(codes) == len(images) == len(names):
            embed = fmte(
                ctx,
                t = "Something odd happened, results may be incorrect. If so, please try another search."   
            )
            await ctx.author.send(embed=embed)
        else:
            embed = fmte(
                ctx,
                t = "{} results found, displaying now...".format(len(codes))
            )
            await ctx.author.send(embed=embed)
        for n in range(min(codes.__len__(), images.__len__(), names.__len__())):
            c = n + 1
            tot = min(codes.__len__(), images.__len__(), names.__len__())

            name = str(names[n])[21:-6][:235]
            code = str(codes[n])
            url = str(images[n])
            embed = fmte(
                ctx,
                t = "{} / {}\n{} [{}]".format(
                    c, 
                    tot, 
                    name, 
                    code
                )
            )
            embed.set_image(url = url)
            await ctx.author.send(embed = embed)


async def setup(bot):
    await bot.add_cog(NSFW(bot))