import asyncio
import functools
from typing import Any
import discord
from discord.ext import commands
import openai

from bot import Builder, BuilderContext
from src.utils.APIFuncs import evaulate_response
from src.utils.Embeds import fmte


class API(commands.Cog):
    def __init__(self, bot: Builder) -> None:
        self.bot = bot
        super().__init__()

    def ge(self):
        return "\N{Clockwise Rightwards and Leftwards Open Circle Arrows}"  # Bruh

    @commands.hybrid_group()
    async def openai(self, ctx: BuilderContext):
        pass

    @openai.command()
    async def detect(self, ctx: BuilderContext, message: str):
        preset = APIPresets.OpenAI.detect(message)
        response: dict = await API.run(
            self.bot.loop, self.bot.openai.Completion.create, **preset
        )
        code: int = int(evaulate_response(response))
        if code == 0:
            embed = fmte(
                ctx,
                t="All Good!",
                d="Nothing worrying was detected in this message.",
                c=discord.Color.teal(),
            )
        elif code == 1:
            embed = fmte(
                ctx,
                t="Hm...",
                d="This one is a bit worrying. It may include sensitive topics, insults, or things of that sort.",
                c=discord.Color.yellow(),
            )
        else:
            embed = fmte(
                ctx,
                t="Nada",
                d="This one crossed the line. It most likely includes slurs, NSFW, etc.",
                c=discord.Color.red(),
            )
        await ctx.send(embed=embed)

    async def run(loop: asyncio.BaseEventLoop, func, *args, **kwargs):
        partial = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, partial)


class APIPresets:
    class OpenAI:
        def detect(text: str):
            return {
                "model": "content-filter-alpha",
                "prompt": f"<|endoftext|>{text}\n--\nLabel:",
                "temperature": 0,
                "max_tokens": 1,
                "top_p": 0,
                "logprobs": 10,
            }


async def setup(bot: Builder):
    await bot.add_cog(API(bot))
