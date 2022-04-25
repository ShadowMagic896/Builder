import discord
from discord import ui, Interaction
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
    # @guilds(871913539936329768)
    async def feedback(self, ctx: commands.Context):
        """
        Opens up a modal where you can send anonymous feedback to the delelopers.
        """
        await ctx.interaction.response.defer()
        await ctx.interaction.response.send_modal(FeedbackModal())


class FeedbackModal(ui.Modal, title="Anonymous Feedback Forum"):
    rating: str = ui.TextInput(
        label="On a general scale of 1 - 10, what do you think about this bot?",
        style=discord.TextStyle.short,
        placeholder="Please give a response...",
        min_length=1,
        max_length=2,
        required=False)

    bugs: str = ui.TextInput(
        label="An average, how ofen do you experiece bugs in the bot?",
        style=discord.TextStyle.short,
        placeholder="Please give a response...",
        max_length=150,
        required=False
    )

    requests: str = ui.TextInput(
        label="Are there any featues / changes to the bot you would like to see? If so, what are they?",
        style=discord.TextStyle.paragraph,
        placeholder="Please give a response...",
        max_length=300,
        required=False)

    comments: str = ui.TextInput(
        label="Is there anything else you would like to tell us? Any and all criticism is more than welcome!",
        style=discord.TextStyle.paragraph,
        placeholder="Please give a response...",
        max_length=300,
        required=False)

    async def on_submit(self, interaction: Interaction) -> None:
        open(
            "feedback.txt",
            "a").write(
            "\n---FEEDBACK---\nRating: %s\nBugs: %s\nReqs: %s\nComments: %s\n\n" %
            (self.rating.strip(),
             self.bugs.strip(),
             self.requests.strip(),
             self.comments.strip()))
        await interaction.response.send_message("Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Client(bot))
