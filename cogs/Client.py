import discord
from discord import TextInput, ui, Interaction
from discord.app_commands import describe, guilds
from discord.ext import commands


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
            "\n---FEEDBACK---\nRating: %s\nBugs: %s\nReqs: %s\nComments: %s\n\n" %
            (self.rating.value.strip(),
             self.bugs.value.strip(),
             self.requests.value.strip(),
             self.comments.value.strip()))
        await interaction.response.send_message("Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Client(bot))
