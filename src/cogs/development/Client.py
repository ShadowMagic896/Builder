import datetime
import io
import discord
from discord import TextInput, ui, Interaction
from discord.app_commands import describe
from discord.ext import commands

import inspect
from typing import List, Optional

from src.auxiliary.user.Converters import Cog, Command, Group
from src.auxiliary.user.Subclass import BaseView
from src.auxiliary.user.UserIO import (
    cog_autocomplete,
    command_autocomplete,
    group_autocomplete,
)
from src.auxiliary.user.Embeds import fmte
from src.auxiliary.bot.Functions import explode


class Client(commands.Cog):
    """
    Commands that manage the bot / how it works
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def ge(self):
        return "\N{ROBOT FACE}"

    @commands.hybrid_command()
    @describe()
    async def invite(self, ctx: commands.Context):
        """
        Gets a link to invite me to a server!
        """
        link = discord.utils.oauth_url(
            self.bot.application_id,
            permissions=discord.Permissions(0),
            scopes=["bot", "applications.commands"],
        )
        embed = fmte(ctx, t="Click the Button Below to Invite Me!")
        view = BaseView(ctx).add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link, label="Invite Me!", url=link
            )
        )

        message = await ctx.send(embed=embed, view=view)
        view.message = message

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
        group="Get all commands of this group",
        command="The command to get the source of.",
    )
    async def source(
        self,
        ctx: commands.Context,
        cog: Optional[Cog],
        group: Optional[Group],
        command: Optional[Command],
    ):
        """
        Gets the source code for any of the bot's commands.
        """
        if not command and not group and not cog:
            embed = fmte(
                ctx,
                t="Source Code!",
                d="[View on GitHub](%s)" % "https://github.com/ShadowMagic896/Builder",
            )
            await ctx.send(embed=embed)
        if command:
            src = command.callback.__code__

            buffer = io.BytesIO()

            src = inspect.getsource(src)
            buffer.write(src.encode("UTF-8"))
            buffer.seek(0)
            embed = fmte(ctx, t=f"Source for Command: {command}")
            file = discord.File(buffer, f"builder.{command}.py")
            await ctx.send(embed=embed, file=file)
        elif group:
            src = "\n\n".join(
                inspect.getsource(c.callback.__code__) for c in explode(group.commands)
            )
            buffer = io.BytesIO()
            buffer.write(src.encode("UTF-8"))
            buffer.seek(0)

            embed = fmte(ctx, t=f"Source for Group: {group.qualified_name}")
            file = discord.File(buffer, f"builder.{group.qualified_name}.py")
            await ctx.send(embed=embed, file=file)
        elif cog:
            buffer = io.BytesIO()
            buffer.write((inspect.getsource(cog.__class__)).encode("UTF-8"))
            buffer.seek(0)

            embed = fmte(ctx, t=f"Source for Cog: `{cog.name}`")
            file = discord.File(buffer, f"builder.{cog.name}.py")
            await ctx.send(embed=embed, file=file)

    @source.autocomplete("cog")
    async def cog_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return await cog_autocomplete(self.bot, inter, current)

    @source.autocomplete("group")
    async def group_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return await group_autocomplete(self.bot, inter, current)

    @source.autocomplete("command")
    async def command_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return await command_autocomplete(self.bot, inter, current)

    @commands.hybrid_command()
    async def disable(
        self, ctx: commands.Context, command: Command, role: Optional[discord.Role]
    ):
        if role is None:
            command = """
                SELECT disabled FROM disabled_commands
                WHERE guildid = $1
            """
        else:
            pass


class FeedbackModal(ui.Modal, title="Anonymous Feedback Forum"):
    rating: TextInput = ui.TextInput(
        label="On a scale of 1 - 10, how useful is Builder?",
        style=discord.TextStyle.short,
        placeholder="Please give a response...",
        min_length=1,
        max_length=2,
        required=False,
    )

    bugs: TextInput = ui.TextInput(
        label="How ofen do you experiece bugs in the bot?",
        style=discord.TextStyle.short,
        placeholder="Please give a response...",
        max_length=150,
        required=False,
    )

    requests: TextInput = ui.TextInput(
        label="Is there anything you want added to the bot?",
        style=discord.TextStyle.paragraph,
        placeholder="Please give a response...",
        max_length=300,
        required=False,
    )

    comments: TextInput = ui.TextInput(
        label="Do you have any other critisism or feedback?",
        style=discord.TextStyle.paragraph,
        placeholder="Please give a response...",
        max_length=300,
        required=False,
    )

    async def on_submit(self, interaction: Interaction) -> None:
        open("data/logs/feedback.txt", "a").write(
            "\n---FEEDBACK---\nRating: {}\nBugs: {}\nReqs: {}\nComments: {}\nAt: {}".format(
                (
                    self.rating.value.strip(),
                    self.bugs.value.strip(),
                    self.requests.value.strip(),
                    self.comments.value.strip(),
                    datetime.datetime.utcnow(),
                )
            )
        )
        await interaction.response.send_message(
            "Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.",
            ephemeral=True,
        )


class SuggestionModal(ui.Modal, title="Suggestion Forum"):
    suggestion: TextInput = discord.ui.TextInput(
        label="What is your suggestion?",
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: Interaction) -> None:
        open("data/logs/suggestions.txt", "a").write(
            "\n---SUGGESTION---\nSuggestion: {}\nAt: {}\nBy: {}".format(
                self.suggestion.value, datetime.datetime.utcnow(), interaction.user
            )
        )
        await interaction.response.send_message(
            "Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Client(bot))
