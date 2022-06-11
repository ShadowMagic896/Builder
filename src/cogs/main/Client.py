import asyncio
from asyncio.subprocess import Process
import datetime
import os
import time
import aiofiles
import io
import discord
from discord import TextInput, ui, Interaction
from discord.app_commands import describe
from discord.ext import commands

import inspect
import psutil
from typing import List, Optional

from src.utils.Converters import Cog, Command, Group
from src.utils.Subclass import BaseModal, BaseView
from src.utils.UserIO import (
    cogAutocomplete,
    groupAutocomplete,
    commandAutocomplete,
)
from src.utils.Embeds import fmte, fmte_i
from src.utils.Functions import explode
from bot import BuilderContext


class Client(commands.Cog):
    """
    Commands that manage the bot / how it works
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.last_updated_log = 0

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
        embed = fmte(ctx, t="Click the Button Below to Invite Me!")
        view = discord.ui.View().add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link, label="Invite Me!", url=link
            )
        )

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
        return await cogAutocomplete(self.bot, inter, current)

    @source.autocomplete("group")
    async def group_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return await groupAutocomplete(self.bot, inter, current)

    @source.autocomplete("command")
    async def command_autocomplete(
        self, inter: discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        return await commandAutocomplete(self.bot, inter, current)

    @commands.hybrid_command()
    async def uptime(self, ctx: BuilderContext):
        """
        Find out how long the bot has been online for
        """
        start = datetime.datetime.fromtimestamp(self.bot.start_unix)
        embed = fmte(ctx, t=f"Last Restart: <t:{round(self.bot.start_unix)}:R>")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def github(self, ctx: BuilderContext):
        """
        Gets the bot's GitHub push log
        """
        if time.time() - self.last_updated_log > 300:
            shell: Process = await asyncio.create_subprocess_shell(
                f"cd /d {os.getcwd()} && git config --global --add safe.directory R:/VSCode-Projects/Discord-Bots/Builder && git log -t --diff-merges=on --max-count 3 > data/logs/git.log"
            )
            await shell.communicate()
            self.last_updated_log = time.time()
        file: discord.File = discord.File(
            "data/logs/git.log",
            filename="repo.diff",
            description="Builder's GitHub repository log",
        )
        embed = fmte(
            ctx,
            t="Showing Git Log",
        )
        await ctx.send(embed=embed, file=file)
        file.close()

    @commands.hybrid_command()
    async def about(self, ctx: BuilderContext):
        """
        Who is this guy, anyways?
        """
        view = ServerInformation(ctx)
        view.message = await ctx.send(embed=await Client.getAboutEmbed(ctx), view=view)

    async def getAboutEmbed(ctx: BuilderContext):
        embed = fmte(
            ctx,
            t=f"About: {ctx.bot.user}",
            d=f"*{(await ctx.bot.application_info()).description}*",
        )
        exp_com = explode(ctx.bot.commands)
        embed.add_field(name="Commands", value=len(exp_com))
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
        super().__init__(ctx, timeout)

    @discord.ui.button(label="Server Information", emoji="\N{DESKTOP COMPUTER}")
    async def serverInfo(self, inter: discord.Interaction, button: discord.ui.Button):
        freq = psutil.cpu_freq(False)
        embed = fmte_i(inter, t="Server Information")
        values = psutil.disk_io_counters(True)
        for name, disk in values.items():
            embed.add_field(
                name=name,
                value=f"ㅤㅤ**Read #:**: `{disk.read_count}`\n"
                f"ㅤㅤ**Read:** `{round(disk.read_bytes / 1000000, 2)}MB`\n"
                f"ㅤㅤ**Write #:** `{disk.write_count}`\n"
                f"ㅤㅤ**Write:** `{round(disk.write_bytes / 1000000, 2)}MB`\n"
                f"ㅤㅤ**Read Time:** `{disk.read_time}ms`\n"
                f"ㅤㅤ**Write Time:** `{disk.write_time}ms`\n",
            )
        embed.add_field(
            name="CPU",
            value=f"ㅤㅤ**CPUs:** `{psutil.cpu_count(True)}`\n"
            f"ㅤㅤ**Percents:** `{psutil.cpu_percent(percpu=False)}`\n"
            f"ㅤㅤ**Frequency:** `{round(freq.current)}Mhz`\n",
        )
        view = ReturnToAbout(self.ctx)
        view.message = await inter.response.edit_message(embed=embed, view=view)


class ReturnToAbout(BaseView):
    def __init__(self, ctx: BuilderContext, timeout: Optional[float] = 300):
        super().__init__(ctx, timeout)

    @discord.ui.button(label="Return", emoji="\N{LEFTWARDS BLACK ARROW}")
    async def ret(self, inter: discord.Interaction, button: discord.Button):
        view = ServerInformation(self.ctx)
        view.message = await inter.response.edit_message(
            embed=await Client.getAboutEmbed(self.ctx), view=view
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Client(bot))
