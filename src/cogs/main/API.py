import discord
from discord.app_commands import describe, Range
from discord.ext import commands

from bot import Builder, BuilderContext
from src.utils.APIFuncs import evaulate_response
from src.utils.Embeds import fmte


class API(commands.Cog):
    """
    Using external APIs! Suggestion one with /suggest
    """

    def __init__(self, bot: Builder) -> None:
        self.bot = bot
        super().__init__()

    def ge(self):
        return "\N{Clockwise Rightwards and Leftwards Open Circle Arrows}"  # Bruh

    @commands.hybrid_group()
    async def openai(self, ctx: BuilderContext):
        pass

    @openai.command()
    @describe(
        message="The message to detect",
    )
    async def filter(self, ctx: BuilderContext, message: str):
        """
        Detects the estimated unsafe content coming from a message. Errs on the side of caution
        """
        preset = APIPresets.OpenAI.detect(message, 1)
        response: dict = await API.run(
            self.bot.loop, self.bot.openai.Completion.create, **preset
        )
        code: int = int(evaulate_response(response))
        if code == 0:
            embed = fmte(
                ctx,
                t="This Text is Safe",
                c=discord.Color.teal(),
            )
        elif code == 1:
            embed = fmte(
                ctx,
                t="This text is sensitive.",
                d="This means that the text could be talking about a sensitive topic, something political, religious, or talking about a protected class such as race or nationality.",
                c=discord.Color.yellow(),
            )
        else:
            embed = fmte(
                ctx,
                t="This text is unsafe.",
                d="This means that the text contains profane language, prejudiced or hateful language, something that could be NSFW, or text that portrays certain groups/people in a harmful manner.",
                c=discord.Color.red(),
            )
        await ctx.send(embed=embed)

    @openai.command()
    @describe(
        message="The message to complete or respond to",
        stochasticism="How random the response is",
    )
    async def complete(
        self, ctx: BuilderContext, message: str, stochasticism: Range[float, 0, 1] = 0.5
    ):
        """
        Autocompltetes a sentence or responds to a question
        """
        preset = APIPresets.OpenAI.complete(message, stochasticism)
        response: dict = await API.run(
            self.bot.loop, self.bot.openai.Completion.create, **preset
        )
        embed = fmte(ctx, t="Completion Finished")
        for choice in response["choices"]:
            embed.add_field(name=f"Choice {choice['index']+1}:", value=choice["text"])
        await ctx.send(embed=embed)

    @openai.command()
    @describe(
        message="The text to fix",
        stochasticism="How random the response is",
    )
    async def grammar(
        self,
        ctx: BuilderContext,
        message: str,
        edits: Range[int, 1, 5] = 1,
        stochasticism: Range[float, 0, 1] = 0.5,
    ):
        """
        Fixes grammar in a statement
        """
        preset = APIPresets.OpenAI.grammar(message, edits, stochasticism)
        response: dict = await API.run(
            self.bot.loop, self.bot.openai.Edit.create, **preset
        )
        embed = fmte(ctx, t="Checking Completed")
        for choice in response["choices"]:
            embed.add_field(name=f"Choice {choice['index']+1}:", value=choice["text"])
        await ctx.send(embed=embed)

    @openai.command()
    @describe(
        message="The message to edit",
        instructions="How to edit the message. The more specific, the better",
        edits="How many times to edit the message",
        stochasticism="How random the response is",
    )
    async def edit(
        self,
        ctx: BuilderContext,
        message: str,
        instructions: str,
        edits: Range[int, 1, 5] = 1,
        stochasticism: Range[float, 0, 1] = 0.5,
    ):
        """
        Attempts to edit a message based upon instructions
        """
        preset = APIPresets.OpenAI.gen_edit(message, instructions, edits, stochasticism)
        response: dict = await API.run(
            self.bot.loop, self.bot.openai.Edit.create, **preset
        )
        embed = fmte(ctx, t="Editing Completed")
        for choice in response["choices"]:
            embed.add_field(name=f"Choice {choice['index']+1}:", value=choice["text"])
        await ctx.send(embed=embed)


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

        def complete(text: str, temp: float):
            return {
                "model": "text-davinci-001",
                "temperature": temp,
                "prompt": text,
                "max_tokens": 2000,
            }

        def grammar(text: str, edits: int, stochasticism: float):
            return {
                "model": "text-davinci-edit-001",
                "input": text,
                "instruction": "Fix all spelling mistakes",
                "temperature": stochasticism,
                "n": edits,
            }

        def gen_edit(text: str, inst: str, edits: int, stochasticism: float):

            return {
                "model": "text-davinci-edit-001",
                "input": text,
                "instruction": inst,
                "temperature": stochasticism,
                "n": edits,
            }


async def setup(bot: Builder):
    await bot.add_cog(API(bot))
