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
from typing import List, Optional

from src.auxUser.UserIO import explode
from src.auxUser.Embeds import Desc, fmte
from src.auxBot.Constants import CONSTANTS


class Client(commands.Cog):
    """
    Commands that manage the bot / how it works.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def ge(self):
        return "\N{ROBOT FACE}"

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
        cog="The cog to get the source of.",
        command="The command to get the source of.",
        ephemeral=Desc.ephemeral
    )
    async def source(self, ctx: commands.Context, cog: Optional[str], command: Optional[str], ephemeral: bool = False):
        """
        Gets the source code for any of the bot's commands.
        """
        if not command and not cog:
            embed = fmte(
                ctx, t="Source Code!", d="[View on GitHub](%s)" %
                "https://github.com/ShadowMagic896/Builder")
            await ctx.send(embed=embed, ephemeral=ephemeral)
        elif command and not cog:
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
        elif cog and not command:
            if not (cog := self.bot.get_cog(cog)):
                raise commands.errors.ExtensionNotFound(cog)
            src = inspect.getsource(cog.__class__)
            buffer = io.BytesIO()
            buffer.write(src.encode("UTF-8"))
            buffer.seek(0)

            embed = fmte(
                ctx,
                t="Source for Cog: %s" % cog.qualified_name
            )
            file = discord.File(buffer, "source.%s.py" % cog.qualified_name)
            await ctx.send(embed=embed, file=file, ephemeral=ephemeral)
        else:
            if not (command := self.bot.get_command(command)):
                raise commands.errors.CommandNotFound(ctx.args[1])
            elif not (cog := self.bot.get_cog(cog)):
                raise commands.errors.ExtensionNotFound(ctx.args[0])
            if command in explode(cog.get_commands()):
                src = command.callback.__code__
                note = ""
            else:
                src = cog.__class__
                note = "# Command not found in that cog, showing source for cog instead.\n"
            buffer = io.BytesIO()
            buffer.write((note + inspect.getsource(src)).encode("UTF-8"))
            buffer.seek(0)

            embed = fmte(
                ctx,
                t="Source for %s" %
                (("`%s`" %
                  cog.qualified_name) if note else "`{}` of Cog `{}`".format(
                    command.qualified_name,
                    cog.qualified_name)))
            file = discord.File(
                buffer, "source.%s.py" %
                (cog.qualified_name if note else command.qualified_name))
            await ctx.send(embed=embed, file=file, ephemeral=ephemeral)

    @source.autocomplete("cog")
    async def cog_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        return sorted([discord.app_commands.Choice(name=c, value=c) for c in list(self.bot.cogs.keys())if ((current.lower() in c.lower(
        ) or (c.lower()) in current.lower())) and c not in CONSTANTS.Cogs().FORBIDDEN_COGS][:25], key=lambda c: c.name)

    @source.autocomplete("command")
    async def command_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        return sorted(
            [
                discord.app_commands.Choice(
                    name="[{}] {}".format(
                        c.cog_name, c.qualified_name), value=c.qualified_name) for c in (
                    explode([c for c in self.bot.commands]) if not getattr(
                        inter.namespace, "cog") else explode(self.bot.get_cog(
                            inter.namespace.cog).get_commands()) if inter.namespace.cog in [
                                c for c, v in self.bot.cogs.items()] else []) if (
                                    (current.lower() in c.qualified_name.lower()) or (
                                        c.qualified_name.lower() in current.lower())) and c.cog_name not in CONSTANTS.Cogs().FORBIDDEN_COGS][
                                            :25], key=lambda c: c.name[
                                                c.name.index("]") + 1:])


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
