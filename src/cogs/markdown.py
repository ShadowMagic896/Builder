import discord
import markdown
import tkinter
import tkinterhtml
import webbrowser
from discord.ext import commands
from typing import Optional
from unidecode import UnidecodeError

from ..utils import errors as berrors
from ..utils.bot_types import Builder, BuilderContext
from ..utils.subclass import BaseCog


class MarkDown(BaseCog):
    """
    Cog for generating and viewing markdown text
    """
    @commands.hybrid_group()
    async def markdown(self, ctx: BuilderContext):
        pass

    @markdown.command()
    async def render(self, ctx: BuilderContext, text: Optional[str], file: Optional[discord.Attachment]):
        if not (text or file):
            raise berrors.MissingArguments("Must supply either text or file")
        md = markdown.markdown
        if file:
            content = await file.read()
            try:
                text: str = content.decode("UTF-8")
            except UnidecodeError:
                raise commands.errors.BadArgument("File contains invalid characters (Not UTF-8)")

        render: str = md(text=text)
        print(render)
    

async def setup(bot: Builder):
    await bot.add_cog(MarkDown(bot))
