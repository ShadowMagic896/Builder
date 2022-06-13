import discord
from discord import app_commands
from discord.app_commands import describe, Range
from discord.ext import commands
from unidecode import unidecode_expect_nonascii

from bot import Builder, BuilderContext
from src.utils.embeds import fmte


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


async def setup(bot: Builder):
    await bot.add_cog(Misc(bot))
