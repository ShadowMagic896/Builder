from html import unescape
from typing import Literal, Optional

import discord
import markdown
from discord.app_commands import describe
from discord.ext import commands

from ..utils.abc import BaseCog
from ..utils.bot_abc import Builder, BuilderContext
from ..utils.errors import MissingArguments


class MarkDown(BaseCog):
    """
    Cog for generating and viewing markdown text
    """

    @commands.hybrid_group()
    async def markdown(self, ctx: BuilderContext):
        pass

    @markdown.command()
    @describe(
        text="The text to escape",
        attachment="The file whose contents to escape",
        as_needed="Whether to escape only the required characters. Imperfect, but works for most cases",
    )
    async def escape(
        self,
        ctx: BuilderContext,
        text: Optional[str],
        attachment: Optional[discord.Attachment],
        as_needed: bool = False,
    ):
        """
        Escape markdown characters in a string
        """
        if attachment is not None:
            content = await attachment.read()
            content = discord.utils.escape_markdown(content, as_needed=as_needed)
            file = discord.File(content, filename=attachment.filename)
            embed = await ctx.format(
                title="Escaped Markdown",
            )
            await ctx.send(file=file, embed=embed)
        else:
            embed = await ctx.format(
                title="Escaped Markdown",
                desc=f"```\n{discord.utils.escape_markdown(text, as_needed=as_needed)}\n```",
            )
            await ctx.send(embed=embed)

    @markdown.command()
    @describe(
        text="The text to unescape",
        attachment="The file whose contents to unescape",
    )
    async def unescape(
        self,
        ctx: BuilderContext,
        text: Optional[str],
        attachment: Optional[discord.Attachment],
    ):
        """
        Unescape markdown characters in a string
        """
        if attachment is not None:
            content = await attachment.read()
            content = content.decode("utf-8").replace("\\", "")
            file = discord.File(content, filename=attachment.filename)
            embed = await ctx.format(
                title="Unescaped Markdown",
            )
            await ctx.send(file=file, embed=embed)
        else:
            text = text.replace("\\", "")
            embed = await ctx.format(
                title="Unescaped Markdown",
                desc=f"```\n{text}\n```",
            )
            await ctx.send(embed=embed)

    @markdown.command()
    @describe(
        text="The text to convert",
        attachment="The file whose contents to convert",
    )
    async def to_html(
        self,
        ctx: BuilderContext,
        text: Optional[str],
        attachment: Optional[discord.Attachment],
        output_format: Optional[Literal["html", "xhtml"]] = "html",
    ):
        """
        Convert markdown text to HTML
        """
        if attachment is not None:
            content = await attachment.read()
            content = markdown.markdown(content, output_format=output_format)
            file = discord.File(content, filename=attachment.filename)
            embed = await ctx.format(
                title="Markdown to HTML",
            )
            await ctx.send(file=file, embed=embed)
        elif text is not None:
            embed = await ctx.format(
                title="Markdown to HTML",
                desc=markdown.markdown(text, output_format=output_format),
            )
            await ctx.send(embed=embed)
        else:
            raise MissingArguments("text")

    @markdown.command()
    async def preview(
        self,
        ctx: BuilderContext,
        text: Optional[str],
        attachment: Optional[discord.Attachment],
    ):
        """
        Allow the user to get a visual preview of markdown text using TKHTMKView
        """
        if attachment is not None:
            pass
        elif text is not None:
            pass
        else:
            raise MissingArguments("text")


async def setup(bot: Builder):
    await bot.add_cog(MarkDown(bot))
