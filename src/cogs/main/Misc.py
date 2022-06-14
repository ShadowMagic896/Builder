import discord
from discord import app_commands
from discord.app_commands import describe, Range
from discord.ext import commands
from unidecode import unidecode_expect_nonascii
import json as js

from bot import Builder, BuilderContext
from src.utils.embeds import fmte
from src.utils.constants import Const


class Misc(commands.Cog):
    """
    Commands that don't fit into any one category
    """

    def __init__(self, bot: Builder) -> None:
        self.bot = bot

    def ge(self):
        return "\N{BLACK QUESTION MARK ORNAMENT}"

    @commands.hybrid_command()
    @describe(message="The message to decancer")
    async def decancer(self, ctx: BuilderContext, message: str):
        """
        Converts a message into plain latin characters
        """
        decoded = unidecode_expect_nonascii(message, errors="ignore")
        embed = fmte(ctx, t="Message Decancered")
        embed.add_field(name="Before", value=message, inline=False)
        embed.add_field(name="After", value=decoded, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def affirmation(self, ctx: BuilderContext):
        url: str = Const.URLs.AFFIRMATION
        response = await self.bot.session.get(url, ssl=False)
        json: dict = await response.json()
        quote: str = json["affirmation"]

        embed = fmte(ctx, t=quote)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def advice(self, ctx: BuilderContext):
        url: str = Const.URLs.ADVICE
        response = await self.bot.session.get(url, ssl=False)
        json: dict = js.loads(await response.text())
        id_, advice = json["slip"]["id"], json["slip"]["advice"]

        embed = fmte(ctx, t=advice, d=f"ID: `{id_}`")
        await ctx.send(embed=embed)


async def setup(bot: Builder):
    await bot.add_cog(Misc(bot))
