import builtins
import datetime
import io
import os
from types import CodeType
import discord
from discord import TextInput, ui, Interaction
from discord.app_commands import describe, guilds
from discord.ext import commands

import inspect
from typing import Optional

from _aux.embeds import Desc, fmte


class Client(commands.Cog):
    """
    Commands that manage the bot / how it works.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def ge(self):
        return "🤖"

    @commands.hybrid_command()
    @commands.cooldown(2, 3600, commands.BucketType.user)
    async def feedback(self, ctx: commands.Context):
        """
        Opens up a modal where you can send anonymous feedback to the delelopers.
        """
        await ctx.interaction.response.send_modal(FeedbackModal())

    @commands.hybrid_command()
    @commands.cooldown(2, 3600, commands.BucketType.user)
    async def suggest(self, ctx: commands.Context):
        """
        Opens up a modal where you can send a suggestion to the delelopers.
        """
        await ctx.interaction.response.send_modal(SuggestionModal())

    @commands.hybrid_command()
    @describe(
        command="The command to get the source of.",
        ephemeral=Desc.ephemeral
    )
    async def source(self, ctx: commands.Context, command: Optional[str], ephemeral: bool = False):
        """
        Gets the source code for any of the bot's commands.
        """
        if not command:
            embed = fmte(
                ctx, t="Source Code!", d="[View on GitHub](%s)" %
                "https://github.com/ShadowMagic896/Builder")
            await ctx.send(embed=embed, ephemeral=ephemeral)
        elif command:
            if not (command := self.bot.get_command(command)):
                raise commands.errors.CommandNotFound(command)
            src = command.callback.__code__

            buffer = io.BytesIO()

            src = inspect.getsource(src)
            buffer.write(src.encode("UTF-8"))
            buffer.seek(0)
            embed = fmte(
                ctx,
                t="Source for Command: %s" % command
            )
            file = discord.File(buffer, "source.%s.py" % command)
            await ctx.send(embed=embed, file=file, ephemeral=ephemeral)

    @source.autocomplete("command")
    async def source_autocomplete(self, inter: discord.Interaction, current: str):
        return [
            discord.app_commands.Choice(name=c.name, value=c.name)
            for c in self.bot.commands if
            (c.cog_name not in os.getenv("FORBIDDEN_COGS").split(";")) and
            (c.qualified_name in current) or
            (current in c.qualified_name)
        ][:25]


class FeedbackModal(ui.Modal, title="Anonymous Feedback Forum"):
    rating: TextInput = ui.TextInput(
        label="On a scale of 1 - 10, how useful is Builder?",
        style=discord.TextStyle.short,
        placeholder="Please give a response...",
        min_length=1,
        max_length=2,
        required=False)

    bugs: TextInput = ui.TextInput(
        label="How ofen do you experiece bugs in the bot?",
        style=discord.TextStyle.short,
        placeholder="Please give a response...",
        max_length=150,
        required=False
    )

    requests: TextInput = ui.TextInput(
        label="Is there anything you want added to the bot?",
        style=discord.TextStyle.paragraph,
        placeholder="Please give a response...",
        max_length=300,
        required=False)

    comments: TextInput = ui.TextInput(
        label="Do you have any other critisism or feedback?",
        style=discord.TextStyle.paragraph,
        placeholder="Please give a response...",
        max_length=300,
        required=False)

    async def on_submit(self, interaction: Interaction) -> None:
        open(
            "data/logs/feedback.txt",
            "a").write(
            "\n---FEEDBACK---\nRating: {}\nBugs: {}\nReqs: {}\nComments: {}\nAt: {}".format(
                (self.rating.value.strip(),
                 self.bugs.value.strip(),
                 self.requests.value.strip(),
                 self.comments.value.strip(),
                 datetime.datetime.utcnow())))
        await interaction.response.send_message("Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.", ephemeral=True)


class SuggestionModal(ui.Modal, title="Suggestion Forum"):
    suggestion: TextInput = discord.ui.TextInput(
        label="What is your suggestion?",
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: Interaction) -> None:
        open(
            "data/logs/suggestions.txt",
            "a").write(
                "\n---SUGGESTION---\nSuggestion: {}\nAt: {}\nBy: {}".format(
                    self.suggestion.value,
                    datetime.datetime.utcnow(),
                    interaction.user
                )
        )
        await interaction.response.send_message("Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Client(bot))
