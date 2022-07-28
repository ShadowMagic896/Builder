import datetime
import inspect
import io
from typing import List, Optional

import aiofiles
import discord
import psutil
from discord import Interaction, TextInput, ui
from discord.app_commands import describe
from discord.ext import commands

from ..utils.bot_types import Builder, BuilderContext
from ..utils.constants import URLs
from ..utils.converters import Cog, Command, Group
from ..utils.functions import explode
from ..utils.abc import BaseCog, BaseModal, BaseView
from ..utils.user_io import (cog_autocomplete, command_autocomplete,
                             group_autocomplete)


class Client(BaseCog):
    """
    Commands that manage the bot / how it works
    """

    def __init__(self, bot: Builder) -> None:
        self.bot = bot

    def ge(self):
        return "\N{ROBOT FACE}"

    @commands.hybrid_command()
    @describe()
    async def invite(self, ctx: BuilderContext):
        """
        Gets a link to invite me to a server!
        """
        link = discord.utils.oauth_url(
            self.bot.application_id,
            permissions=discord.Permissions(0),
            scopes=["bot", "applications.commands"],
        )
        embed = await ctx.format(title="Click the Button Below to Invite Me!")
        view = InviteView(link)

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    @describe(anonymous="Whether to send the feedback anonymously or not")
    @commands.cooldown(2, 60 * 60, commands.BucketType.user)
    async def bug(self, ctx: BuilderContext, anonymous: bool = False):
        """
        Opens up a modal where you can send anonymous bug feedback to the developers
        """
        await ctx.interaction.response.send_modal(BugReportModal(ctx, anonymous))

    @commands.hybrid_command()
    @describe(anonymous="Whether to send the feedback anonymously or not")
    @commands.cooldown(2, 60 * 60, commands.BucketType.user)
    async def suggest(self, ctx: BuilderContext, anonymous: bool = False):
        """
        Opens up a modal where you can send anonymous suggestions to the developers
        """
        await ctx.interaction.response.send_modal(SuggestionModal(ctx, anonymous))

    @commands.hybrid_command()
    @describe(anonymous="Whether to send the feedback anonymously or not")
    @commands.cooldown(2, 60 * 60, commands.BucketType.user)
    async def feedback(self, ctx: BuilderContext, anonymous: bool = False):
        """
        Opens up a modal where you can send anonymous feedback to the developers
        """
        await ctx.interaction.response.send_modal(FeedbackModal(ctx, anonymous))

    @commands.hybrid_command()
    @describe(
        cog="The cog to get the source of.",
        group="Get all commands of this group",
        command="The command to get the source of.",
    )
    async def source(
        self,
        ctx: BuilderContext,
        cog: Optional[Cog],
        group: Optional[Group],
        command: Optional[Command],
    ):
        """
        Gets the source code for any of the bot's commands.
        """
        if not command and not group and not cog:
            embed = await ctx.format(
                title="Source Code!",
                desc=f"[View on GitHub]({URLs.REPO})",
            )
            await ctx.send(embed=embed)
        if command:
            src = command.callback.__code__

            buffer = io.BytesIO()

            src = inspect.getsource(src)
            buffer.write(src.encode("UTF-8"))
            buffer.seek(0)
            embed = await ctx.format(title=f"Source for Command: {command}")
            file = discord.File(buffer, f"builder.{command}.py")
            await ctx.send(embed=embed, file=file)
        elif group:
            src = "\n\n".join(
                inspect.getsource(c.callback.__code__) for c in explode(group.commands)
            )
            buffer = io.BytesIO()
            buffer.write(src.encode("UTF-8"))
            buffer.seek(0)

            embed = await ctx.format(title=f"Source for Group: {group.qualified_name}")
            file = discord.File(buffer, f"builder.{group.qualified_name}.py")
            await ctx.send(embed=embed, file=file)
        elif cog:
            buffer = io.BytesIO()
            buffer.write((inspect.getsource(cog.__class__)).encode("UTF-8"))
            buffer.seek(0)

            embed = await ctx.format(title=f"Source for Cog: `{cog.name}`")
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
    async def uptime(self, ctx: BuilderContext):
        """
        Find out how long the bot has been online for
        """
        start = datetime.datetime.fromtimestamp(self.bot.start_unix)
        embed = await ctx.format(
            title=f"Last Restart: <t:{round(self.bot.start_unix)}:R>"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def about(self, ctx: BuilderContext):
        """
        Who is this guy, anyways?
        """
        view = ServerInformation(ctx)
        view.message = await ctx.send(embed=await Client.getAboutEmbed(ctx), view=view)

    async def getAboutEmbed(ctx: BuilderContext):
        embed = await ctx.format(
            title=f"About: {ctx.bot.user}",
            desc=f"*{(await ctx.bot.application_info()).description}*",
        )
        exp_com = explode(ctx.bot.commands)
        embed.add_field(name="Commands", value=len([v for v in exp_com]))
        embed.add_field(
            name="Groups",
            value=(
                len(
                    {x for x in ctx.bot.commands if isinstance(x, commands.HybridGroup)}
                )
            ),
        )
        embed.add_field(name="Cogs", value=len(ctx.bot.cogs))
        embed.add_field(name="Guilds", value=f"{len(ctx.bot.guilds):,}")
        embed.add_field(
            name="Members",
            value=f"{sum({g.member_count for g in ctx.bot.guilds}):,}",
        )
        embed.add_field(name="Shards", value=f"{ctx.bot.shard_count or 1:,}")
        return embed


class FeedbackModal(BaseModal):
    def __init__(self, ctx: BuilderContext, anon: bool) -> None:
        self.anon = anon
        super().__init__(title=f"{ctx.author}: Feedback Forum")

    rating: TextInput = ui.TextInput(
        label="On a scale of 1 - 10, how useful is Builder to you?",
        style=discord.TextStyle.short,
        placeholder="Please give a response...",
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
        async with aiofiles.open("data/logs/users/feedback.log", "a") as file:
            vals = ["\n".join([self.rating, self.bugs, self.requests, self.comments])]
            formatted = f"{datetime.datetime.now()}: {interaction.user if not self.anon else 'Anonymous'} from {interaction.guild} [{interaction.guild.id}]\n{vals}\n\n"
            await file.write(formatted)
        await interaction.response.send_message(
            "Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.",
            ephemeral=True,
        )


class SuggestionModal(BaseModal):
    def __init__(self, ctx: BuilderContext, anon: bool) -> None:
        self.anon = anon
        super().__init__(title=f"{ctx.author}: Suggestion Forum", timeout=600)

    suggestion: TextInput = discord.ui.TextInput(
        label="What is your suggestion?",
        placeholder="Please give a response...",
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: Interaction) -> None:
        async with aiofiles.open("data/logs/users/suggestions.log", "a") as file:
            formatted = f"{datetime.datetime.now()}: {interaction.user if not self.anon else 'Anonymous'} from {interaction.guild} [{interaction.guild.id}]\n{self.suggestion.value}\n\n"
            await file.write(formatted)
        await interaction.response.send_message(
            "Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.",
            ephemeral=True,
        )


class BugReportModal(BaseModal):
    def __init__(self, ctx: BuilderContext, anon: bool):
        self.anon = anon
        super().__init__(title=f"{ctx.author}: Bug Report Forum", timeout=600)

    bug: TextInput = discord.ui.TextInput(
        label="Relavant information about the command",
        placeholder="Please give a response...",
        style=discord.TextStyle.long,
    )

    async def on_submit(self, interaction: Interaction) -> None:
        async with aiofiles.open("data/logs/users/bugs.log", "a") as file:
            formatted = f"{datetime.datetime.now()}: {interaction.user if not self.anon else 'Anonymous'} from {interaction.guild} [{interaction.guild.id}]\n{self.bug.value}\n\n"
            await file.write(formatted)
        await interaction.response.send_message(
            "Thank you for your feedback! We look at every single forum, and we respect both your opinion and privacy.",
            ephemeral=True,
        )


class ServerInformation(BaseView):
    def __init__(self, ctx: BuilderContext, timeout: Optional[float] = 300):
        self.ctx = ctx
        super().__init__(ctx, timeout)

    @discord.ui.button(label="Server Information", emoji="\N{DESKTOP COMPUTER}")
    async def server_info(self, inter: discord.Interaction, button: discord.ui.Button):
        embed = await self.ctx.format(title="Server Information")
        freq = psutil.cpu_freq(percpu=False)
        values = psutil.disk_io_counters(perdisk=True)
        for name, disk in values.items():
            embed.add_field(
                name=name,
                value=f"\\~\\~**Read #:**: `{disk.read_count}`\n"
                f"\\~\\~**Read:** `{round(disk.read_bytes / 1000000, 2)}MB`\n"
                f"\\~\\~**Write #:** `{disk.write_count}`\n"
                f"\\~\\~**Write:** `{round(disk.write_bytes / 1000000, 2)}MB`\n"
                f"\\~\\~**Read Time:** `{disk.read_time}ms`\n"
                f"\\~\\~**Write Time:** `{disk.write_time}ms`\n",
            )
        embed.add_field(
            name="CPU",
            value=f"\\~\\~**CPUs:** `{psutil.cpu_count(True)}`\n"
            f"\\~\\~**Percents:** `{psutil.cpu_percent(percpu=False)}`\n"
            f"\\~\\~**Frequency:** `{round(freq.current)}Mhz`\n",
        )
        view = ReturnToAbout(self.ctx)
        view.message = await inter.response.edit_message(embed=embed, view=view)


class ReturnToAbout(BaseView):
    def __init__(self, ctx: BuilderContext, timeout: Optional[float] = 300):
        super().__init__(ctx, timeout)

    @discord.ui.button(label="Return", emoji="\N{LEFTWARDS BLACK ARROW}")
    async def go_back(self, inter: discord.Interaction, button: discord.Button):
        view = ServerInformation(self.ctx)
        view.message = await inter.response.edit_message(
            embed=await Client.getAboutEmbed(self.ctx), view=view
        )


class InviteView(discord.ui.View):
    def __init__(self, url: str, *, timeout: Optional[float] = 180):
        self.url = url
        super().__init__(timeout=timeout)
        self.add_item(
            discord.ui.Button(
                label="Invite Me!",
                emoji="\N{ENVELOPE}",
                style=discord.ButtonStyle.link,
                url=url,
            )
        )

    @discord.ui.button(label="Raw Link", emoji="\N{LINK SYMBOL}")
    async def raw_link(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.send_message(self.url, ephemeral=True)


async def setup(bot: Builder):
    await bot.add_cog(Client(bot))
