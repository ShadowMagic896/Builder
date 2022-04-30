import asyncio
import io
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

import os


from PIL import Image, ImageDraw, ImageColor
from typing import Literal, Optional


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
        return fn[fn.replace(".", "_", fn.count(".") - 1).index(".")+1:]

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

    @commands.hybrid_group()
    async def image(self, ctx: commands.Context):
        pass

    @image.command()
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

    @image.command()
    @commands.cooldown(10, 60 * 60, commands.BucketType.user)
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

    @image.command()
    @commands.cooldown(10, 60 * 60, commands.BucketType.user)
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
        Adds text to an image. More featues are a WIP
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
    
    @image.command()
    @describe(
        attachment = "The image to crop.",
        left = "The left point to start cropping.",
        upper = "The upper point to start cropping.",
        right = "The right point to stop cropping.",
        lower = "The lower point to start cropping.",
        ephemeral=Desc.ephemeral,
    )
    async def crop(
        self, 
        ctx: commands.Context, 
        attachment: discord.Attachment, 
        left: int, upper: int, right: int, lower: int,
        ephemeral: bool = False,
        ):
        """
        Crops an image to the given dimensions
        """
        buffer = io.BytesIO()
        await attachment.save(buffer)
        buffer.seek(0)

        img: Image.Image = Image.open(buffer)
        buffer = io.BytesIO()
        img = img.crop((left, upper, right, lower))
        img.save(buffer, self.getExtension(attachment))
        buffer.seek(0)

        embed = fmte(
            ctx,
            t="Image Cropped"
        )
        file = discord.File(buffer, "crop.%s" % attachment.filename)
        await ctx.send(embed=embed, file=file, ephemeral=ephemeral)
    
    @image.command()
    @describe(
        attachment = "The image to get information on.",
        ephemeral=Desc.ephemeral,
    )
    async def info(self, ctx: commands.Context, attachment: discord.Attachment, ephemeral: bool = False):
        """
        Retrieves information about the image
        """
        embed = fmte(
            ctx,
            t = "Gathered Information",
        )
        embed.add_field(
            name = "Dimensions",
            value = "`{}x{}`".format(attachment.width, attachment.height),
            inline=False
        )
        embed.add_field(
            name = "File Size",
            value = "`%s bytes`" % attachment.size,
            inline=False
        )
        embed.add_field(
            name = "File Type",
            value = "`%s`" % attachment.content_type,
            inline=False
        )
        buffer = io.BytesIO()
        await attachment.save(buffer)
        buffer.seek(0)
        file = discord.File(buffer, filename=attachment.filename)
        await ctx.send(embed=embed, file=file, ephemeral=ephemeral)

    @image.command()
    @describe(
        attachment = "The image to rotate",
        degrees = "The amount of degrees to rotate the image.",
        centerx = "The X Coordinate of the center of rotation.",
        centery = "The Y Coordinate of the center of rotation.",
        fillcolor = "The color to fill the remaining parts of the image after rotation.",
        ephemeral = Desc.ephemeral
    )
    async def rotate(
        self, 
        ctx: commands.Context, 
        attachment: discord.Attachment, 
        degrees: int, 
        centerx: Optional[int] = None, centery: Optional[int] = None,
        fillcolor: str = "white",
        ephemeral: bool = False,
        ):
        """
        Rotates an image by a given amount of degrees
        """
        buffer = io.BytesIO()
        await attachment.save(buffer)
        buffer.seek(0)
        if not (centerx and centery):
            center = None
        else:
            center = (centerx, centery)

        img = Image.open(buffer)
        fillcolor = ImageColor.getrgb(fillcolor)
        img = img.rotate(degrees, center=center, fillcolor=fillcolor, expand=True)
        buffer = io.BytesIO()
        img.save(buffer, self.getExtension(attachment))
        buffer.seek(0)

        embed = fmte(
            ctx,
            t = "Image Rotated"
        )
        file = discord.File(buffer, "rotate.%s" % attachment.filename)
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Media(bot))
