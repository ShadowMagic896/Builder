from re import T
from typing import ContextManager
import discord
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError  

import asyncio
import math
import random
import requests
from bs4 import BeautifulSoup

from _aux.embeds import fmte

class NSFW(commands.Cog):
    @commands.hybrid_group()
    async def nsfw(self, ctx: commands.Context):
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
        query = query.split(" ")
        if not ctx.channel.is_nsfw:
            return
        async with ctx.typing():
            res = requests.get(
                f"https://rule34.xxx/index.php?page=post&s=list&tags={'+'.join(query)}+"
            ).text
            soup = BeautifulSoup(res, 'html.parser')
            img = soup.find_all("img")

            data = []
            for im in img[2:43]:
                data.append(im["src"])
            data = [random.choice(data), random.choice(
                data), random.choice(data)]

            embed = fmte(
                ctx,
                t = "Image(s) returned!",
                d = "This bot is not responsible for any image returned."
            )
            await ctx.send(embed=embed)
            for d in data:
                if not d.startswith("https:"):
                    d = "https:" + d
                embed = fmte(
                    ctx
                )
                embed.set_image(url=d)
                await ctx.send(embed=embed)

    @nsfw.command(aliases=["rule34stream", "r34stream", "rule34s"])
    async def r34s(self, ctx: commands.Context, *, query: str):
        query = query.split(" ")
        async with ctx.typing():
            res = requests.get(
                f"https://rule34.xxx/index.php?page=post&s=list&tags={'+'.join(query)}+"
            ).text
            soup = BeautifulSoup(res, 'html.parser')
            img = soup.find_all("img")

            data = []
            for im in img[2:43]:

                data.append(im["src"])

            embed = fmte(
                ctx,
                t="Image(s) returned!",
                d="This bot is not responsible for any image returned.",
            )
            await ctx.send(embed=embed)
            
            for d in data:
                if not d.startswith("https:"):
                    d = "https:" + d
                embed = fmte( ctx, )
                embed.set_image(url=d)
                await ctx.send(embed = embed)
                await asyncio.sleep(1)

    @nsfw.command()
    async def neko(self, ctx: commands.Context, amount: int = 1):
        if ctx.author.id not in [724811595976409119, 742060021214478387]:
            await ctx.send("Sorry, you can't use this command... try being DivineEnding or Cookie.")
            return
        if 1 < amount > 10:
            raise CommandInvokeError("Invalid amount")

        async with ctx.typing():
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
    async def nekolewd(self, ctx: commands.Context, amount: int = 1):
        # if ctx.author.id not in [724811595976409119, 742060021214478387]:
        #     await ctx.send("Sorry, you can't use this command... try being DivineEnding or Cookie.")
        #     return
        if not ctx.channel.is_nsfw:
            return
        if 1 < amount > 10:
            raise CommandInvokeError("Invalid amount")
        async with ctx.typing():
            data = []
            for co in range(amount):
                res = requests.get(
                    f"https://nekos.life/lewd"
                ).text
                soup = BeautifulSoup(res, 'html.parser')
                img = soup.find_all("img")
                data.append(img[0]["src"])
            embed = fmte(
                ctx,
                t = "Image(s) returned!",
                description="This bot is not responsible for any image returned.",
            )
            await ctx.send(embed=embed)
            for l in data:
                embed = fmte( ctx, )
                embed.set_image(url=l)
                await ctx.send(embed=embed)

    @nsfw.command(aliases=["nhg", "nh"])
    async def nhentai(self, ctx: commands.Context, code: int):
        if not ctx.channel.is_nsfw:
            return
        res = requests.get(f"https://nhentai.xxx/g/{code}").text
        soup = BeautifulSoup(res, "html.parser")
        data = [
            img["src"] 
            for img in soup.find_all("img")
        ][1:-5]
        
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
        for co, x in enumerate(data):
            embed = fmte(
                ctx,
                t=f"{co+1} / {len(data)}: {code}",
            )
            embed.set_image(url=x)
            await ctx.author.send(embed=embed)

    @nsfw.command(aliases=["nhs", "nhentaisearch"])
    async def nhsearch(self, ctx: commands.Context, *, query: str):
        url = "https://nhentai.xxx/search/?q={}".format('+'.join(query.split(" ")))
        res = requests.get(url).text
        parse = BeautifulSoup(
            res, "html.parser"
        )

        links = [
            i["src"] 
            for i in parse.find_all(
                "img"
            )[1:] 
            if i["src"].startswith(
                "https://"
            )
        ]
        print(links)
        print(str(parse))
        found = [
            str(i).split()[2][9:-2] 
            for i in parse.find_all(
                "a", href=True
            )
        ].__len__()

        ids = [
            str(i).split()[2][9:-2] 
            for i in parse.find_all(
                "a", href=True
            )[25:found-23]]

        titles = [
            i.text for i in parse.find_all(
            "a", href=True)[25:found-23]
        ]

        embed = fmte(
            ctx,
            t = f"Check your DMs, {ctx.author}"
        )
        await ctx.reply(embed=embed)
        embed = fmte(
            ctx,
            t="Image(s) returned!",
            d="This bot is not responsible for any image returned.",
        )
        await ctx.author.send(embed=embed)
        for co, ele in enumerate(links[:math.min(links.__len__(),  10)]):
            embed = fmte(
                ctx,
                t=titles[co],
                d=f"ID: {ids[co]}",
            )
            embed.set_image(url=links[co])
            await ctx.author.send(embed=embed)


async def setup(bot):
    await bot.add_cog(NSFW(bot))