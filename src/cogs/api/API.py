import asyncio
import functools
import discord
from discord.ext import commands

from bot import BuilderContext


class API(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    def ge(self):
        return "\N{Clockwise Rightwards and Leftwards Open Circle Arrows}"  # Bruh

    @commands.hybrid_group()
    async def openai(self, ctx: BuilderContext):
        pass

    @openai.command()
    async def detect(self, ctx: BuilderContext, message: str):
        self.bot.openai
        pass

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
