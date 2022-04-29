import asyncio
import io
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

import os

import numpy as np

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.lines import Line2D


from PIL import Image, ImageDraw
from typing import Literal, Optional

import matplotlib
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox

from _aux.embeds import fmte, Desc
from _aux.Converters import ListConverter


class Media(commands.Cog):
    """
    Commands to manipulate and change images, download videos, and more!
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def ge(self):
        return "🖼️"

    def getExtension(self, attachment: discord.Attachment):
        fn = attachment.filename
        return fn[fn.replace(".", "_", fn.count(".") - 1).index("."):]

    def getFP(self, attachment: discord.Attachment):
        return "data/PIL/image%s%s" % (str(len(os.listdir("data/PIL"))),
                                       self.getExtension(attachment))

    def checkAttachment(self, attachment: discord.Attachment):
        if attachment.size > 40000000:
            raise IOError(
                "Attachment is too large. Please keep files under 40MB")

    async def _resize(self, attachment: discord.Attachment, width, height) -> io.BytesIO:
        buffer = io.BytesIO()
        await attachment.save(buffer)
        buffer.seek(0)

        img = Image.open(buffer)
        img = img.resize((width, height))

        buffer = io.BytesIO()  # Reset the buffer

        img.save(buffer, "png")
        img.close()
        buffer.seek(0)

        return buffer

    @commands.hybrid_command()
    @commands.cooldown(5, 60 * 60 * 3, commands.BucketType.user)
    @describe(
        width="The new image's width.",
        height="The new image's height.",
        ephemeral=Desc.ephemeral,
    )
    async def resize(self, ctx: commands.Context, attachment: discord.Attachment, width: int, height: int, ephemeral: bool = False):
        """
        Resizes an image to a certain width and height
        """
        self.checkAttachment(attachment)
        ogsize = (attachment.width, attachment.height)

        buffer: io.BytesIO = await self._resize(attachment, width, height)

        embed = fmte(
            ctx,
            t="Image successfully resized!",
            d="File of dimensions (%s, %s) converted to file of dimensions (%s, %s)" %
            (ogsize[0], ogsize[1], width, height)
        )

        file = discord.File(buffer, filename="resize.%s" % attachment.filename)
        await ctx.send(embed=embed, file=file, ephemeral=ephemeral)

    @commands.hybrid_command()
    @commands.cooldown(2, 60 * 60 * 3, commands.BucketType.user)
    @describe(
        name="What to name the new emoji.",
        reason="The reason for creating the emoji. Shows up in audit logs.",
        ephemeral=Desc.ephemeral,
    )
    async def steal(self, ctx: commands.Context, name: str, attachment: discord.Attachment, reason: Optional[str] = "No reason given", ephemeral: bool = False):
        """
        Copies an image attachment and adds it to the guild as an emoji
        """
        self.checkAttachment(attachment)
        extension = self.getExtension(attachment)

        if extension.lower() not in [".png", ".jpg"]:
            raise TypeError(
                "Only PNG and JPG files are permitted. [Discord limitation]")

        fp = self.getFP(attachment)

        buffer = io.BytesIO()

        await attachment.save(buffer)

        buffer = await self._resize(attachment, 128, 128)

        e: discord.Emoji = await ctx.guild.create_custom_emoji(name=name, image=buffer.read(), reason=reason)
        embed = fmte(
            ctx,
            t="Emoji created!",
            d="**Emoji:** %s\n**Name:** %s\n**Reason:** %s" %
            ("<:{}:{}>".format(e.name, e.id), e.name, reason)
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    @commands.cooldown(2, 60 * 60 * 3, commands.BucketType.user)
    @describe(
        text="The text to add.",
        attachment="The image to add the text to.",
        xpos="The X-Position for the top-left corner of the text.",
        ypos="The Y-Position for the top-left corner of the text.",

        # direction = "The direction of the text. Right to left, Left to Right, or Top to Bottom.",
        # align = "Where to align the text. Left, Center, or Right.",

        # font = "The font to use.",
        # strokeweight = "The width of the font, in pixels.",

        r="The RED component of the text color.",
        g="The GREEN component of the text color.",
        b="The BLUE component of the text color.",
        ephemeral=Desc.ephemeral,
    )
    async def text(
        self,
        ctx: commands.Context,
        text: str,
        attachment: discord.Attachment,
        xpos: int, ypos: int,

        # direction: Literal["rtl", "ltr", "ttb"] = "rtl",
        # align: Literal["left", "center", "right"] = "left",

        # font: str = "C:\\Windows\\Fonts\\PERTILI.TTF",
        # strokeweight: Range[int, 1, 75] = 5,

        r: Range[int, 0, 255] = 255,
        g: Range[int, 0, 255] = 255,
        b: Range[int, 0, 255] = 255,

        ephemeral: bool = False
    ):
        """
        Adds text to an image. Does this have too many
        """

        buffer = io.BytesIO()

        await attachment.save(buffer)
        buffer.seek(0)
        img = Image.open(buffer)
        drawer = ImageDraw.Draw(img)

        drawer.text(
            (xpos, ypos),
            text, fill=(r, g, b),
            # direction=direction,
            # align=align,
            # font=font
        )
        buffer = io.BytesIO()
        img.save(buffer, "png")
        buffer.seek(0)
        file = discord.File(buffer, filename="text.%s" % attachment.filename)
        embed = fmte(
            ctx,
            t="File Successfully Edited!"
        )
        await ctx.send(embed=embed, file=file, ephemeral=ephemeral)

    @commands.hybrid_command()
    @describe(
        user=Desc.user,
        ephemeral=Desc.ephemeral
    )
    async def avatar(self, ctx: commands.Context, user: Optional[discord.Member], ephemeral: bool = False):
        """
        Gets the avatar / profile picture of a member
        """
        user = user if user else ctx.author
        embed = fmte(
            ctx,
            t="%s's Avatar" % user.display_name,
            d="[View Link](%s)" % user.avatar.url
        )
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_group()
    async def graph(self, ctx: commands.Context):
        pass

    @graph.command()
    @describe(
        xvalues="An array of numbers, seperated by a comma. Example: 1, 298, -193, 2.2",
        yvalues="An array of numbers, seperated by a comma. Example: 1, 298, -193, 2.2",
        xlabel="The label of the graph's X axis.",
        ylabel="The label of the graph's Y axis.",
        title="The title of the graph",
        color="The color of the line.",
        autoscale="Whether to autoscale / autozoom the axes.",
    )
    async def plot(
        self,
        ctx: commands.Context,

        xvalues: ListConverter,
        yvalues: ListConverter,

        xlabel: str = "X Axis",
        ylabel: str = "X Axis",

        title: Optional[str] = None,
        color: str = "black",

        autoscale: bool = False
    ):
        """
        Graphs X-Values and Y-Values using matplotlib and shows the result
        """

        buffer = io.BytesIO()

        plt.plot(xvalues, yvalues, color=color)

        plt.grid(True)

        plt.title(title if title else str(ctx.author))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        minv = min(min(xvalues), min(yvalues))
        maxv = max(max(xvalues), max(yvalues))

        if not autoscale:
            plt.xlim(minv, maxv)
            plt.ylim(minv, maxv)

        plt.autoscale(autoscale)

        plt.minorticks_on()

        plt.savefig(buffer)

        buffer.seek(0)
        embed = fmte(
            ctx,
            t="Data Loaded and Graphed"
        )
        file = discord.File(buffer, filename="graph.png")
        await ctx.send(embed=embed, file=file)

    @plot.autocomplete("color")
    async def plotcolor_autocomplete(self, inter: discord.Interaction, current: str):
        colors = [
            "aqua",
            "aquamarine",
            "axure",
            "beige",
            "black",
            "blue",
            "brown",
            "chartreuse",
            "chocolate",
            "coral",
            "crimson",
            "cyan",
            "darkblue",
            "darkgreen",
            "fuchsia",
            "gold",
            "goldenrod",
            "green",
            "grey",
            "indigo",
            "ivory",
            "khaki",
            "lavender",
            "lightblue",
            "lightgreen",
            "lime",
            "magenta",
            "maroon",
            "navy",
            "olive",
            "orange",
            "orangered",
            "orchid",
            "pink",
            "plum",
            "purple",
            "red",
            "salmon",
            "sienna",
            "silver",
            "tan",
            "teal",
            "tomato",
            "turquoise",
            "violet",
            "wheat",
            "white",
            "yellow",
            "yellowgreen"]
        return [
            discord.app_commands.Choice(name=c, value=c)
            for c in colors if
            c in current or current in c
        ][:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(Media(bot))
