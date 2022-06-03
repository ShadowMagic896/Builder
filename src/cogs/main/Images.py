import asyncio
import io
from io import BytesIO
import functools
import os
import discord
from discord.app_commands import describe, Range
from discord.ext import commands


from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from typing import Any, Callable, Literal, Optional

from data import Config

from src.auxiliary.user.Embeds import fmte, Desc


class Images(commands.Cog):
    """
    Commands to manipulate and format images
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.loop = self.bot.loop

    def ge(self):
        return "\N{FRAME WITH PICTURE}\N{VARIATION SELECTOR-16}"

    def getExtension(self, image: discord.Attachment):
        fn = image.filename
        return fn[fn.replace(".", "_", fn.count(".") - 1).index(".") + 1 :]

    def checkAttachment(self, image: discord.Attachment):
        if image.size > 40000000:
            raise IOError("Attachment is too large. Please keep files under 40MB")

    async def run(self, func: Callable, *args, **kwargs) -> Any:
        """
        Runs a synchronous method in the current async loop's executor
        All *args and **kwargs get passed to the function
        """
        partial = functools.partial(func, *args, **kwargs)
        return await asyncio.get_event_loop().run_in_executor(None, partial)

    def callOnImage(self, buffer: BytesIO, function: str, *args, **kwargs) -> Any:
        img = Image.open(buffer)
        img: Image.Image = getattr(img, function)(*args, **kwargs)
        buffer: io.BytesIO = io.BytesIO()
        img.save(buffer, "png")
        buffer.seek(0)
        return buffer

    def callForEnhance(self, buffer: BytesIO, function: str, *args, **kwargs) -> Any:
        img = Image.open(buffer)
        img: Image.Image = getattr(ImageEnhance, function)(img).enhance(*args, **kwargs)
        buffer: io.BytesIO = io.BytesIO()
        img.save(buffer, "png")
        buffer.seek(0)
        return buffer

    async def tobuf(self, image: discord.Attachment, check: bool = True) -> io.BytesIO:
        if check:
            self.checkAttachment(image)

        buffer: io.BytesIO = io.BytesIO()
        await image.save(buffer)
        buffer.seek(0)
        return buffer

    async def toimg(self, image: discord.Attachment, check: bool = True) -> Image.Image:
        return Image.open(await self.tobuf(image, check))

    @commands.hybrid_group()
    async def image(self, ctx: commands.Context):
        pass

    @image.command()
    @commands.cooldown(5, 60 * 60 * 3, commands.BucketType.user)
    @describe(
        width="The new image's width.",
        height="The new image's height.",
    )
    async def resize(
        self, ctx: commands.Context, image: discord.Attachment, width: int, height: int
    ):
        """
        Resizes an image to a certain width and height
        """
        ogsize = (image.width, image.height)

        buffer: io.BytesIO = await self.run(
            self.callOnImage, await self.tobuf(image), "resize", (width, height)
        )

        embed = fmte(
            ctx,
            t="Image successfully resized!",
            d="File of dimensions (%s, %s) converted to file of dimensions (%s, %s)"
            % (ogsize[0], ogsize[1], width, height),
        )

        file = discord.File(buffer, filename="resize.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @commands.cooldown(10, 60 * 60, commands.BucketType.user)
    @describe(
        name="What to name the new emoji.",
        reason="The reason for creating the emoji. Shows up in audit logs.",
    )
    async def steal(
        self,
        ctx: commands.Context,
        name: str,
        image: discord.Attachment,
        reason: Optional[str] = "No reason given",
    ):
        """
        Copies an image image and adds it to the guild as an emoji
        """

        buffer: io.BytesIO = await self.run(
            self.callOnImage, await self.tobuf(image), "resize", (128, 128)
        )

        e: discord.Emoji = await ctx.guild.create_custom_emoji(
            name=name, image=buffer.read(), reason=reason
        )
        embed = fmte(
            ctx,
            t="Emoji created!",
            d="**Emoji:** %s\n**Name:** %s\n**Reason:** %s"
            % ("<:{}:{}>".format(e.name, e.id), e.name, reason),
        )
        await ctx.send(embed=embed)

    @image.command()
    @commands.cooldown(10, 60 * 60, commands.BucketType.user)
    @describe(
        text="The text to add.",
        image="The image to add the text to.",
        xpos="The X-Position for the top-left corner of the text.",
        ypos="The Y-Position for the top-left corner of the text.",
        font="The font to use.",
        strokeweight="The width of the font, in pixels.",
        r="The RED component of the text color.",
        g="The GREEN component of the text color.",
        b="The BLUE component of the text color.",
    )
    async def text(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        text: str,
        xpos: int,
        ypos: int,
        font: str = "pertili",
        strokeweight: Range[int, 1, 200] = 5,
        r: Range[int, 0, 255] = 255,
        g: Range[int, 0, 255] = 255,
        b: Range[int, 0, 255] = 255,
    ):
        """
        Adds text to an image.
        """
        font = font.lower()
        if font not in [p.lower() for p in os.listdir(Config.FONT_PATH)]:
            raise ValueError("Not a valid font. Please use the autocomplete.")
        try:
            font = ImageFont.FreeTypeFont(Config.FONT_PATH + font, strokeweight)
        except BaseException as e:
            print(e)
        img = await self.toimg(image)

        await self.run(
            lambda i: i.text(xy=(xpos, ypos), text=text, fill=(r, g, b), font=font),
            ImageDraw.ImageDraw(img),
        )

        buffer: BytesIO = BytesIO()
        img.save(buffer, "png")
        buffer.seek(0)

        file = discord.File(buffer, filename="text.%s" % image.filename)

        embed = fmte(ctx, t="File Successfully Edited!")
        await ctx.send(embed=embed, file=file)

    @text.autocomplete(name="font")
    async def textfont_autocomplete(self, inter: discord.Interaction, current: str):
        return [
            discord.app_commands.Choice(name=p[:-4], value=p)
            for p in os.listdir(Config.FONT_PATH)
            if (p.lower() in current.lower() or current.lower() in p.lower())
            and p.lower().endswith(".ttf")
        ][:25]

    @image.command()
    @describe(
        image="The image to crop.",
        left="The left point to start cropping.",
        upper="The upper point to start cropping.",
        right="The right point to stop cropping.",
        lower="The lower point to start cropping.",
    )
    async def crop(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        left: int,
        upper: int,
        right: int,
        lower: int,
    ):
        """
        Crops an image to the given dimensions
        """
        buffer: BytesIO = await self.run(
            self.callOnImage,
            await self.tobuf(image),
            "crop",
            (left, upper, right, lower),
        )

        embed = fmte(ctx, t="Image Cropped")
        file = discord.File(buffer, "crop.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(
        image="The image to get information on.",
    )
    async def info(self, ctx: commands.Context, image: discord.Attachment):
        """
        Retrieves information about the image
        """
        embed = fmte(
            ctx,
            t="Gathered Information",
        )
        embed.add_field(
            name="Dimensions",
            value="`{}x{}`".format(image.width, image.height),
            inline=False,
        )
        embed.add_field(name="File Size", value="`%s bytes`" % image.size, inline=False)
        embed.add_field(
            name="File Type", value="`%s`" % image.content_type, inline=False
        )
        file = discord.File(await self.tobuf(image), filename=image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(
        image="The image to rotate",
        degrees="The amount of degrees to rotate the image.",
        centerx="The X Coordinate of the center of rotation.",
        centery="The Y Coordinate of the center of rotation.",
        fillcolor="The color to fill the remaining parts of the image after rotation.",
    )
    async def rotate(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        degrees: int,
        centerx: Optional[int] = None,
        centery: Optional[int] = None,
        fillcolor: str = "white",
    ):
        """
        Rotates an image by a given amount of degrees
        """
        buffer: BytesIO = await self.run(
            self.callOnImage,
            await self.tobuf(image),
            "rotate",
            degrees,
            center=(
                centerx or round(image.width / 2),
                centery or round(image.height / 2),
            ),
            fillcolor=fillcolor,
            expand=True,
        )

        embed = fmte(ctx, t="Image Rotated")
        file = discord.File(buffer, "rotate.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    def getFilters(self):
        """Basically get all constants in ImageFilter"""
        return [c for c in dir(ImageFilter) if c.upper() == c]

    @image.command()
    @describe(
        image="The image to apply the filter to.",
        filter="The filter to apply.",
    )
    async def filter(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        filter: str,
    ):
        """
        Applies a filter onto the image
        """
        filts = self.getFilters()
        if filter not in filts:
            raise commands.BadArgument(filter)

        filter: ImageFilter = getattr(ImageFilter, filter)
        buffer: BytesIO = await self.run(
            self.callOnImage, await self.tobuf(image), "filter", filter
        )

        embed = fmte(ctx, t="Image Filter Applied")
        file = discord.File(buffer, "filter.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @filter.autocomplete("filter")
    async def filterimagefilter_autocomplete(
        self, inter: discord.Interaction, current: str
    ):
        return [
            discord.app_commands.Choice(name=c, value=c)
            for c in self.getFilters()
            if c.lower() in current.lower() or current.lower() in c.lower()
        ][:25]

    @image.command()
    @describe(image="The image to convert.")
    async def greyscale(self, ctx: commands.Context, image: discord.Attachment):
        """
        Convert an image to a grey-scale color scheme
        """
        buffer: BytesIO = await self.run(
            self.callOnImage, await self.tobuf(image), "convert", "L"
        )

        embed = fmte(ctx, t="Conversion Complete")
        file = discord.File(buffer, "gs.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(image="The image to convert", mode="The Image Type to convert to")
    async def convert(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        mode: Literal[
            "1",
            "CMYK",
            "F",
            "HSV",
            "I",
            "L",
            "LAB",
            "P",
            "RGB",
            "RGBA",
            "RGBX",
            "YCbCr",
        ],
    ):
        """
        Attempts to convert the image into the specified mode.
        """
        buffer = await self.run(
            self.callOnImage, await self.tobuf(image), "convert", mode
        )

        embed = fmte(ctx, t="Image Successfully Converted")
        file = discord.File(buffer, "conv.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(image="The image to transform", size="The output size of the image")
    async def transform(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        method: Literal["EXTENT", "AFFINE", "PERSPECTIVE", "QUAD", "MESH"],
        size: Optional[int],
    ):
        """
        Transforms an image's colors, pixel by pixel using a method.
        """
        buffer: BytesIO = self.run(
            self.callOnImage,
            await self.tobuf(image),
            "transform",
            size=size or image.size,
            method=getattr(Image, method),
        )

        embed = fmte(ctx, t="Image Successfully Transformed")
        file = discord.File(buffer, "trfr.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(image="The image to flip", method="How to flip the image")
    async def flip(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        method: Literal[
            "FLIP_LEFT_RIGHT", "FLIP_TOP_BOTTOM", "TRANSPOSE", "TRANSVERSE"
        ],
    ):
        """
        Flips an image.
        """
        buffer: BytesIO = await self.run(
            self.callOnImage,
            await self.tobuf(image),
            "transpose",
            method=getattr(Image, method),
        )

        embed = fmte(ctx, t="Image Successfully Flipped")
        file = discord.File(buffer, "trps.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(image="The image to invert")
    async def invert(self, ctx: commands.Context, image: discord.Attachment):
        """
        Inverts an image's colors.
        """

        buffer: BytesIO = await self.run(
            self.callOnImage, await self.tobuf(image), "convert", "L"
        )

        embed = fmte(ctx, t="Image Successfully Inverted")
        file = discord.File(buffer, "invr.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.group()
    async def enhance(self, ctx: commands.Context):
        pass

    @enhance.command()
    @describe(
        image="The image whose contrast to adjust.",
        factor="The factor of contrast. 0 is greyscale, 100 is maximum contrast.",
    )
    async def contrast(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        factor: Range[float, 0, 100],
    ):
        """
        Adjusts the contrast of an image.
        """
        buffer: BytesIO = self.callForEnhance(
            await self.tobuf(image), "Contrast", factor
        )

        embed = fmte(ctx, t="Image Successfully Edited")
        file = discord.File(buffer, "cntr.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @enhance.command()
    @describe(
        image="The image whose contrast to adjust.",
        factor="The factor of brightness. 0 is black, 100 is basically pure white.",
    )
    async def brightness(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        factor: Range[float, 0, 100],
    ):
        """
        Adjusts the brightness of an image.
        """
        buffer: BytesIO = self.callForEnhance(
            await self.tobuf(image), "Brightness", factor
        )

        embed = fmte(ctx, t="Image Successfully Edited")
        file = discord.File(buffer, "brht.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @enhance.command()
    @describe(
        image="The image whose contrast to adjust.",
        factor="The factor of brightness. 0 is black & white.",
    )
    async def color(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        factor: Range[float, 0, 100],
    ):
        """
        Adjusts the color of an image.
        """
        buffer: BytesIO = self.callForEnhance(await self.tobuf(image), "Color", factor)

        embed = fmte(ctx, t="Image Successfully Edited")
        file = discord.File(buffer, "brht.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @enhance.command()
    @describe(
        image="The image whose contrast to adjust.",
        factor="The factor of brightness. 0 is blurred.",
    )
    async def sharpness(
        self,
        ctx: commands.Context,
        image: discord.Attachment,
        factor: Range[float, 0, 100],
    ):
        """
        Adjusts the sharpess of an image.
        """
        buffer: BytesIO = self.callForEnhance(
            await self.tobuf(image), "Sharpness", factor
        )

        embed = fmte(ctx, t="Image Successfully Edited")
        file = discord.File(buffer, "shrp.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @commands.hybrid_command()
    @describe(
        user=Desc.user,
    )
    async def avatar(self, ctx: commands.Context, user: Optional[discord.Member]):
        """
        Gets the avatar / profile picture of a member.
        """
        user = user if user else ctx.author
        embed = fmte(
            ctx,
            t="%s's Avatar" % user.display_name,
            d="[View Link](%s)" % user.avatar.url,
        )
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Images(bot))
