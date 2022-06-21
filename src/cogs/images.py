import asyncio
import io
from io import BytesIO
import functools
import os
import re
import aiohttp
import discord
from discord.app_commands import describe, Range
from discord.ext import commands


from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from typing import (
    Any,
    Callable,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
)
import numpy as np
from src.utils.functions import filter_similar
from src.utils.colors import to_hex
from src.utils.converters import RGB
from src.utils.subclass import BaseCog, BaseView
from src.utils.static import typehints
from src.utils.coro import run

from wand import image as wimage

import environ

from src.utils.embeds import fmte, Desc
from src.utils import constants
from src.utils.bot_types import Builder, BuilderContext
from src.utils.static import parameters


class Images(BaseCog):
    """
    Commands to manipulate and format images
    """

    def ge(self):
        return "\N{FRAME WITH PICTURE}\N{VARIATION SELECTOR-16}"

    def get_extension(self, image: discord.Attachment):
        fn = image.filename
        return fn[fn.replace(".", "_", fn.count(".") - 1).index(".") + 1 :]

    def check_attachment(self, image: discord.Attachment):
        if image.size > 40000000:
            raise IOError("Attachment is too large. Please keep files under 40MB")

    @commands.hybrid_group()
    async def image(self, ctx: BuilderContext):
        pass

    @image.command()
    @commands.cooldown(5, 60 * 60 * 3, commands.BucketType.user)
    @describe(
        width="The new image's width.",
        height="The new image's height.",
    )
    async def resize(
        self, ctx: BuilderContext, image: discord.Attachment, width: int, height: int
    ):
        """
        Resizes an image to a certain width and height
        """
        ogsize = (image.width, image.height)

        buffer: io.BytesIO = await run(
            PILFN.callOnImage, await PILFN.tobuf(image), "resize", (width, height)
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
        ctx: BuilderContext,
        name: str,
        image: discord.Attachment,
        reason: Optional[str] = "No reason given",
    ):
        """
        Copies an image image and adds it to the guild as an emoji
        """

        buffer: io.BytesIO = await run(
            PILFN.callOnImage, await PILFN.tobuf(image), "resize", (128, 128)
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
    @describe(
        image="The image to crop.",
        left="The left point to start cropping.",
        upper="The upper point to start cropping.",
        right="The right point to stop cropping.",
        lower="The lower point to start cropping.",
    )
    async def crop(
        self,
        ctx: BuilderContext,
        image: discord.Attachment,
        left: int,
        upper: int,
        right: int,
        lower: int,
    ):
        """
        Crops an image to the given dimensions
        """
        buffer: BytesIO = await run(
            PILFN.callOnImage,
            await PILFN.tobuf(image),
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
    async def info(self, ctx: BuilderContext, image: discord.Attachment):
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
        file = discord.File(await PILFN.tobuf(image), filename=image.filename)
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
        ctx: BuilderContext,
        image: discord.Attachment,
        degrees: int,
        centerx: Optional[int] = None,
        centery: Optional[int] = None,
        fillcolor: str = "white",
    ):
        """
        Rotates an image by a given amount of degrees
        """
        buffer: BytesIO = await run(
            PILFN.callOnImage,
            await PILFN.tobuf(image),
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

    def get_filters(self):
        """Basically get all constants in ImageFilter"""
        return [c for c in dir(ImageFilter) if c.upper() == c]

    @image.command()
    @describe(
        image="The image to apply the filter to.",
        filter="The filter to apply.",
    )
    async def filter(
        self,
        ctx: BuilderContext,
        image: discord.Attachment,
        filter: str,
    ):
        """
        Applies a filter onto the image
        """
        filts = self.get_filters()
        if filter not in filts:
            raise commands.BadArgument(filter)

        filter: ImageFilter = getattr(ImageFilter, filter)
        buffer: BytesIO = await run(
            PILFN.callOnImage, await PILFN.tobuf(image), "filter", filter
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
            for c in self.get_filters()
            if c.lower() in current.lower() or current.lower() in c.lower()
        ][:25]

    @image.command()
    @describe(image="The image to convert.")
    async def greyscale(self, ctx: BuilderContext, image: discord.Attachment):
        """
        Convert an image to a grey-scale color scheme
        """
        buffer: BytesIO = await run(
            PILFN.callOnImage, await PILFN.tobuf(image), "convert", "L"
        )

        embed = fmte(ctx, t="Conversion Complete")
        file = discord.File(buffer, "gs.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(image="The image to convert", mode="The Image Type to convert to")
    async def convert(
        self,
        ctx: BuilderContext,
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
        buffer = await run(PILFN.callOnImage, await PILFN.tobuf(image), "convert", mode)

        embed = fmte(ctx, t="Image Successfully Converted")
        file = discord.File(buffer, "conv.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(
        image="The image to invert",
    )
    async def invert(
        self,
        ctx: BuilderContext,
        image: discord.Attachment,
    ):
        """
        Inverts an image's colors
        """
        img: Image.Image = await PILFN.toimg(image)
        array = np.array(img)
        array = 255 - array
        img = Image.frombuffer("RGB", (image.width, image.height), array)
        embed = fmte(ctx, t="Image Successfully Inverted")
        embed, file = await PILFN.spawnItems(embed, img)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(
        image="The image to encipher",
        phrase="The passphrase to encipher the image with.",
    )
    async def encipher(
        self, ctx: BuilderContext, image: discord.Attachment, phrase: str
    ):
        """Enciphers an image using a passphrase, which can be deciphered later."""
        img = await WandImageFunctions.fromAttachment(image)
        await WandImageFunctions.apply(img.encipher, phrase)
        embed = fmte(
            ctx, t="Image Enciphered", d=f"Passphrase to decipher: ||{phrase}||"
        )
        embed, file = await WandImageFunctions.spawnItems(embed, img)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(
        image="The image to decipher",
        phrase="The passphrase to decipher the image with.",
    )
    async def decipher(
        self, ctx: BuilderContext, image: discord.Attachment, phrase: str
    ):
        """Deciphers an image from a passphrase."""
        img = await WandImageFunctions.fromAttachment(image)
        await WandImageFunctions.apply(img.decipher, phrase)
        embed = fmte(
            ctx,
            t="Image Deciphered",
            d=f"Passphrase used to decipher: ||{phrase}||\nIf it didn't come out correctly, remember to save, not copy, the image to decipher and that the passphase is case-sensitive.",
        )
        embed, file = await WandImageFunctions.spawnItems(embed, img)
        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(image="The image to manipulate")
    async def manipulate(self, ctx: BuilderContext, image: discord.Attachment):
        """
        Opens up a large menu to transform and edit an image in many ways.
        """
        buffer: BytesIO = await PILFN.tobuf(image)

        view = ImageManipulateView(ctx, buffer)
        embed = fmte(ctx, t="Currently Applied Filters")
        url = image.url or image.proxy_url or None
        if url is None:
            raise commands.errors.MessageNotFound("Cannot find image for message.")
        embed.set_image(url=url)
        await view.initialCheck()
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @image.command()
    @describe(
        image="The image to get the colors of", to_find="How many colors to look for."
    )
    async def colors(
        self,
        ctx: BuilderContext,
        image: discord.Attachment,
        to_find: Literal[4, 8, 12, 16] = 8,
    ):
        """
        Gets the most common colors in an image.
        """
        buffer: BytesIO = BytesIO()
        await image.save(buffer)
        buffer.seek(0)
        asImage = Image.open(buffer)
        asImage: Image.Image = await run(asImage.convert, "RGBA")

        target_colors = to_find
        in_line: int = 4

        sort = sorted(asImage.getcolors(2**24), key=lambda x: x[0], reverse=True)[
            :100
        ]
        sort = [value[1] for value in sort]
        values = (await filter_similar(sort, 0, 10))[:target_colors]

        fp = ".\\assets\\PIL\\basePaintTemplate.png"
        template = Image.open(fp)
        template = template.convert("RGBA")

        rendered_templates: List[Image.Image] = []

        for color in values:
            result = await run(PILFN.replaceColor, template, (0, 0, 0, 255), color)

            draw = ImageDraw.ImageDraw(result, mode="RGBA")
            as_hex = to_hex(color[:-1])
            font = self.bot.caches.fonts.bookosbi
            inverse = 255 - np.array(color)
            draw.text(
                (round(result.width / 4), round(result.height / 2)),
                f"RGBA{tuple(color)}\n          {as_hex}",
                tuple(inverse)[:-1],
                font,
            )
            rendered_templates.append(result)
        w: int = template.width
        h: int = template.height
        base = Image.new(
            "RGBA", (w * in_line, h * (len(rendered_templates) // in_line) or h)
        )
        for no, im in enumerate(rendered_templates):
            # box = (0, no * h, w, (no + 1) * h) # All vertical

            # We do a bit of math :troll:
            box = [no % in_line * w, no // in_line * h]

            # Add BL vals because PIL can't use self.size ig
            box.extend([box[0] + w, box[1] + h])

            await run(base.paste, im=im, box=box)

        embed = fmte(ctx, t="Colors Retrieved")
        embed, file = await PILFN.spawnItems(embed, base)
        embed.set_thumbnail(url=image.url)

        await ctx.send(embed=embed, file=file)

    @image.command()
    @describe(
        fromcolor="The color to replace, as RBG[A] values separated by a comma.",
        tocolor="The color to replace as, as RBG[A] values separated by a comma.",
    )
    async def replace(
        self,
        ctx: BuilderContext,
        image: discord.Attachment,
        fromcolor: RGB(True, 255),
        tocolor: RGB(True, 255),
        leniency: Optional[int] = 3,
        mode: Literal["By Channel", "By Pixel"] = "By Channel",
    ):
        """
        Replaces any color with another, with some leniency. Colors an also contain an Alpha value.
        """
        img: Image.Image = await PILFN.toimg(image)
        array = np.array(img)
        array[...] = array
        img = Image.fromarray(array, mode="RGBA")

        embed = fmte(ctx, t="Colors Swapped")
        embed.add_field(name="From:", value=fromcolor)
        embed.add_field(name="To:", value=tocolor)
        embed, file = await PILFN.spawnItems(embed, img)
        await ctx.send(embed=embed, file=file)

    @image.group()
    async def enhance(self, ctx: BuilderContext):
        pass

    @enhance.command()
    @describe(
        image="The image whose contrast to adjust.",
        factor="The factor of contrast. 0 is greyscale, 100 is maximum contrast.",
    )
    async def contrast(
        self,
        ctx: BuilderContext,
        image: discord.Attachment,
        factor: Range[float, 0, 100],
    ):
        """
        Adjusts the contrast of an image.
        """
        buffer: BytesIO = PILFN.callForEnhance(
            await PILFN.tobuf(image), "Contrast", factor
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
        ctx: BuilderContext,
        image: discord.Attachment,
        factor: Range[float, 0, 100],
    ):
        """
        Adjusts the brightness of an image.
        """
        buffer: BytesIO = PILFN.callForEnhance(
            await PILFN.tobuf(image), "Brightness", factor
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
        ctx: BuilderContext,
        image: discord.Attachment,
        factor: Range[float, 0, 100],
    ):
        """
        Adjusts the color of an image.
        """
        buffer: BytesIO = PILFN.callForEnhance(
            await PILFN.tobuf(image), "Color", factor
        )

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
        ctx: BuilderContext,
        image: discord.Attachment,
        factor: Range[float, 0, 100],
    ):
        """
        Adjusts the sharpess of an image.
        """
        buffer: BytesIO = PILFN.callForEnhance(
            await PILFN.tobuf(image), "Sharpness", factor
        )

        embed = fmte(ctx, t="Image Successfully Edited")
        file = discord.File(buffer, "shrp.%s" % image.filename)
        await ctx.send(embed=embed, file=file)

    @commands.hybrid_command()
    @describe(
        user=Desc.user,
    )
    async def avatar(self, ctx: BuilderContext, user: typehints.USER = parameters.USER):
        """
        Gets the avatar / profile picture of a member.
        """
        user = user if user else ctx.author
        embed = fmte(
            ctx,
            t="%s's Avatar" % user.display_name,
            d="[View Link](%s)" % user.display_avatar.url,
        )
        embed.set_image(url=user.display_avatar.url)

        class _GView(BaseView):
            def __init__(self, ctx: BuilderContext, timeout: Optional[float] = 300):
                super().__init__(ctx, timeout)

            @discord.ui.button(label="View Profile Avatar")
            async def get(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.avatar is None:
                    inter.user.avatar = inter.user.default_avatar
                embed = fmte(
                    ctx,
                    t="%s's Avatar" % user,
                    d=f"[View Link]({(user.avatar or inter.user.default_avatar).url})",
                )
                embed.set_image(url=(user.avatar or inter.user.default_avatar).url)
                await inter.message.edit(embed=embed, view=_NView(ctx))

            @discord.ui.button(emoji="\N{CROSS MARK}", style=discord.ButtonStyle.danger)
            async def close(self, inter: discord.Interaction, _: Any):
                for c in self.children:
                    c.disabled = True
                try:
                    await inter.response.edit_message(view=self)
                except (discord.NotFound, AttributeError):
                    pass

        class _NView(BaseView):
            def __init__(self, ctx: BuilderContext, timeout: Optional[float] = 300):
                super().__init__(ctx, timeout)

            @discord.ui.button(label="View Guild Avatar")
            async def get(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.avatar is None:
                    inter.user.avatar = inter.user.default_avatar
                embed = fmte(
                    ctx,
                    t="%s's Avatar" % user,
                    d=f"[View Link]({user.display_avatar.url})",
                )
                embed.set_image(url=user.display_avatar.url)
                await inter.message.edit(embed=embed, view=_GView(ctx))

            @discord.ui.button(
                label="Close", emoji="\N{CROSS MARK}", style=discord.ButtonStyle.danger
            )
            async def close(self, inter: discord.Interaction, _: Any):
                for c in self.children:
                    c.disabled = True
                try:
                    await inter.response.edit_message(view=self)
                except (discord.NotFound, AttributeError):
                    pass

        await ctx.send(embed=embed, view=_GView(ctx))


class PILFN:
    def callOnImage(buffer: BytesIO, function: str, *args, **kwargs) -> Any:
        ri = kwargs.pop("ri")
        img = Image.open(buffer)
        img: Image.Image = getattr(img, function)(*args, **kwargs)
        if ri:
            return img
        buffer: io.BytesIO = io.BytesIO()
        img.save(buffer, "png")
        buffer.seek(0)
        return buffer

    def callForEnhance(buffer: BytesIO, function: str, *args, **kwargs) -> Any:
        img = Image.open(buffer)
        img: Image.Image = getattr(ImageEnhance, function)(img).enhance(*args, **kwargs)
        buffer: io.BytesIO = io.BytesIO()
        img.save(buffer, "png")
        buffer.seek(0)
        return buffer

    async def tobuf(image: discord.Attachment, check: bool = True) -> io.BytesIO:
        if check:
            pass
            # self.checkAttachment(image)

        buffer: io.BytesIO = io.BytesIO()
        await image.save(buffer)
        buffer.seek(0)
        return buffer

    async def toimg(image: discord.Attachment, check: bool = True) -> Image.Image:
        return Image.open(await PILFN.tobuf(image, check))

    def replaceColor(
        img: Image.Image,
        fromcolor: Tuple[int, int, int, Optional[int]],
        tocolor: Tuple[int, int, int, Optional[int]],
        leniency: int = 0,
    ) -> Image.Image:
        img = img.copy()

        fromcolor = list(fromcolor)
        if len(fromcolor) == 3:
            fromcolor.append(0)
        tocolor = list(tocolor)
        if len(tocolor) == 3:
            tocolor.append(0)

        data = np.array(img)
        data[(abs(data - fromcolor) <= leniency).all(axis=-1)] = tocolor
        return Image.fromarray(data, mode="RGBA")

    def conformToArray(ar1: List[int], ar2: List[int], leaniency: float = 2):
        return all([abs(ar1[x] - ar2[x]) <= leaniency for x in range(len(ar2))])

    async def spawnItems(
        embed: discord.Embed, image: Image.Image
    ) -> Tuple[discord.Embed, discord.File]:
        buffer = BytesIO()
        image.save(buffer, "PNG")
        buffer.seek(0)

        file = discord.File(fp=buffer, filename="image.png")
        embed.set_image(url="attachment://image.png")

        return embed, file


class WandImageFunctions:
    async def fromAttachment(attachment: discord.Attachment) -> wimage.Image:
        buffer: BytesIO = BytesIO()
        await attachment.save(buffer)
        buffer.seek(0)

        img: wimage.Image = wimage.Image(blob=buffer)
        return img

    async def spawnItems(
        embed: discord.Embed, image: wimage.Image
    ) -> Tuple[discord.Embed, discord.File]:
        buffer = BytesIO()
        image.save(buffer)
        buffer.seek(0)

        file = discord.File(fp=buffer, filename="image.png")
        embed.set_image(url="attachment://image.png")

        return embed, file

    async def apply(func, *args, **kwargs):
        part = functools.partial(func, *args, **kwargs)
        await asyncio.get_event_loop().run_in_executor(None, part)


class ImageManipulateView(BaseView):
    def __init__(
        self, ctx: BuilderContext, buffer: BytesIO, timeout: Optional[float] = 45
    ):
        self.initial = buffer
        self.img = wimage.Image(blob=self.initial)
        self.last = None
        self.filters = []

        self._protected_buttons = ["back", "rev", "finish"]
        super().__init__(ctx, timeout)

    async def initialCheck(self):
        self.back.disabled = True

    async def apply(self, func, *args, **kwargs):
        self.last = self.img.clone()
        part = functools.partial(func, *args, **kwargs)
        await self.ctx.bot.loop.run_in_executor(None, part)

    async def update(self, inter: discord.Interaction, button: discord.ui.Button):
        if button.custom_id != "back":
            self.filters.append(button.label)

        buffer: BytesIO = BytesIO()
        self.img.save(buffer)
        buffer.seek(0)

        embed = fmte(
            self.ctx, t="Effect Applied", d=f"Total Effects: {', '.join(self.filters)}"
        )
        file = discord.File(fp=buffer, filename="image.png")
        embed.set_image(url="attachment://image.png")

        self = await self.check_buttons(button)
        try:
            await inter.response.edit_message(
                embed=embed,
                attachments=[
                    file,
                ],
                view=self,
            )
        except discord.InteractionResponded:
            await (await inter.original_message()).edit(
                embed=embed,
                attachments=[
                    file,
                ],
                view=self,
            )

    async def check_buttons(self, button: discord.ui.Button):
        for i in self.children:
            if (
                isinstance(i, discord.ui.Button)
                and i.custom_id not in self._protected_buttons
            ):
                if i == button:
                    i.style = discord.ButtonStyle.green
                else:
                    i.style = discord.ButtonStyle.blurple
        if self.last is None:
            self.back.disabled = True
        else:
            self.back.disabled = False

        return self

    @discord.ui.button(label="AutoLevel")
    async def autolevel(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.auto_level)
        await self.update(inter, button)

    @discord.ui.button(label="AutoOrient")
    async def autoorient(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.auto_orient)
        await self.update(inter, button)

    @discord.ui.button(label="Blur")
    async def blur(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.adaptive_blur, sigma=1.5)
        await self.update(inter, button)

    @discord.ui.button(label="+Contrast")
    async def pcontrast(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.contrast, False)
        await self.update(inter, button)

    @discord.ui.button(label="-Contrast")
    async def mcontrast(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.contrast, True)
        await self.update(inter, button)

    @discord.ui.button(label="Decipher")
    async def decipher(self, inter: discord.Interaction, button: discord.ui.Button):
        prompt = "Please enter a **PASSPHRASE:**"
        passphrase = (
            await self.getUserInput(
                self.ctx,
                ((), {"embed": fmte(self.ctx, prompt)}),
            )
        ).content
        await self.apply(self.img.decipher, passphrase)
        await self.update(inter, button)

    @discord.ui.button(label="Emboss")
    async def emboss(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.emboss)
        await self.update(inter, button)

    @discord.ui.button(label="Encipher")
    async def encipher(self, inter: discord.Interaction, button: discord.ui.Button):
        prompt = "Please enter a **PASSPHRASE:**"
        passphrase = (
            await self.getUserInput(self.ctx, ((), {"embed": fmte(self.ctx, prompt)}))
        ).content
        await self.apply(self.img.encipher, passphrase)
        await self.update(inter, button)

    @discord.ui.button(label="Equalize")
    async def equalize(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.equalize)
        await self.update(inter, button)

    @discord.ui.button(label="Flip")
    async def flip(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.flip)
        await self.update(inter, button)

    @discord.ui.button(label="Flop")
    async def flop(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.flop)
        await self.update(inter, button)

    @discord.ui.button(label="Sharpen")
    async def sharpen(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.adaptive_sharpen, sigma=1.5)
        await self.update(inter, button)

    @discord.ui.button(label="Painting")
    async def painting(self, inter: discord.Interaction, button: discord.ui.Button):
        await self.apply(self.img.oil_paint)
        await self.update(inter, button)

    @discord.ui.button(label="Paste")
    async def paste(self, inter: discord.Interaction, button: discord.ui.Button):
        prompt: str = "Please send the image to paste..."
        ext_data: str = (
            "You can also send a link, or reply to a message with an image or link."
        )
        img: wimage.Image = await self.getUserInput(
            self.ctx,
            ((), {"embed": fmte(self.ctx, prompt, ext_data)}),
            post_process=ImageManipulateView.getImageFrom,
            post_process_arguments=([self.ctx], {}),
        )

        prompt: str = f"What operator should I use?"
        ext_data = (
            f"Send one of the following: {', '.join(wimage.COMPOSITE_OPERATORS[1:])}"
        )
        op: str = await self.getUserInput(
            self.ctx,
            ((), {"embed": fmte(self.ctx, prompt, ext_data)}),
            post_process=lambda m: m.content.lower(),
        )
        if op not in wimage.COMPOSITE_OPERATORS:
            raise ValueError("Invalid image paste operator.")

        prompt = "Please send the **X VALUE** for where to paste, from the top-left corner of the image."
        x = await self.getUserInput(
            self.ctx,
            ((), {"embed": fmte(self.ctx, prompt)}),
            post_process=self.uint_check,
        )
        if x > self.img.width:
            raise ValueError("X Position is greater than image width.")

        prompt = "Please send the **Y VALUE** for where to paste, from the top-left corner of the image."
        y = await self.getUserInput(
            self.ctx,
            ((), {"embed": fmte(self.ctx, prompt)}),
            post_process=self.uint_check,
        )
        if y > self.img.height:
            raise ValueError("X Position is greater than image width.")

        await self.apply(self.img.composite, img, x, y, operator=op)
        await self.update(inter, button)

    @discord.ui.button(label="Resize")
    async def resize(self, inter: discord.Interaction, button: discord.ui.Button):
        prompt: str = "Please enter a new **WIDTH** value:"
        w = await self.getUserInput(
            self.ctx,
            ((), {"embed": fmte(self.ctx, prompt)}),
            post_process=self.uint_check,
        )

        prompt: str = "Please enter a new **HEIGHT** value:"
        h = await self.getUserInput(
            self.ctx,
            ((), {"embed": fmte(self.ctx, prompt)}),
            post_process=self.uint_check,
        )

        await self.apply(self.img.adaptive_resize, w, h)
        await self.update(inter, button)

    @discord.ui.button(label="Rotate")
    async def rotate(self, inter: discord.Interaction, button: discord.ui.Button):
        prompt: str = "Please enter a **DEGREES** value:"
        degs = await self.getUserInput(
            self.ctx,
            ((), {"embed": fmte(self.ctx, prompt)}),
            post_process=self.degs_check,
        )

        await self.apply(self.img.rotate, degs)
        await self.update(inter, button)

    @discord.ui.button(
        emoji=constants.Const.Emojis().BBARROW_ID,
        label="Revert",
        style=discord.ButtonStyle.red,
        row=4,
        custom_id="rev",
    )
    async def revert(self, inter: discord.Interaction, button: discord.Button):
        self.initial.seek(0)
        self.img = wimage.Image(blob=self.initial)
        self.filters = []
        self.back.disabled = True
        await self.update(inter, button)

    @discord.ui.button(
        emoji=constants.Const.Emojis().BARROW_ID,
        label="Back",
        style=discord.ButtonStyle.gray,
        row=4,
        custom_id="back",
    )
    async def back(self, inter: discord.Interaction, button: discord.Button):
        self.img = self.last
        self.last = None
        self.filters = self.filters[:-1]
        await self.update(inter, button)

    @discord.ui.button(
        emoji="\N{WHITE HEAVY CHECK MARK}",
        label="Finish",
        style=discord.ButtonStyle.gray,
        row=4,
        custom_id="finish",
    )
    async def finish(self, inter: discord.Interaction, button: discord.Button):
        await self.on_timeout()
        embed = (await self.ctx.interaction.original_message()).embeds[0]
        embed.title = "Manipulation Finished"
        embed.description = f"Effects: {', '.join(self.filters)}"

        buffer: BytesIO = BytesIO()
        self.img.save(buffer)
        buffer.seek(0)

        file = discord.File(fp=buffer, filename="image.png")
        embed.set_image(url="attachment://image.png")
        button.style = discord.ButtonStyle.green
        await inter.response.edit_message(
            embed=embed,
            attachments=[
                file,
            ],
            view=self,
        )
        self.stop()

    async def getUserInput(
        self,
        ctx: BuilderContext,
        prompt_data: Tuple[Optional[List[Any]], Optional[Mapping[str, Any]]],
        *,
        check: Callable[[BuilderContext], bool] = None,
        post_process: Callable[
            [
                Any,
            ],
            Any,
        ] = None,
        post_process_arguments: Tuple[List[Any], Mapping[str, Any]] = ([], {}),
    ):
        check = check or (lambda c: c.author == ctx.author and c.channel == ctx.channel)
        args = prompt_data[0] if len(prompt_data) >= 1 else ()
        kwargs = prompt_data[1] if len(prompt_data) >= 2 else {}
        kwargs.update({"ephemeral": True})
        await ctx.interaction.followup.send(*args, **kwargs)
        response = await ctx.bot.wait_for("message", check=check)

        if post_process is None:
            return response

        if asyncio.iscoroutinefunction(post_process):
            return await post_process(
                *post_process_arguments[0], response, **post_process_arguments[1]
            )
        else:
            return post_process(
                *post_process_arguments[0], response, **post_process_arguments[1]
            )

    async def uint_check(self, inp: discord.Message):
        num: int = int(inp.content.strip())
        try:
            await inp.delete()
        except BaseException:
            pass
        if num < 0:
            raise ValueError("This number must be positive")
        return num

    async def degs_check(self, inp: discord.Message):
        num: float = float(inp.content.strip())
        try:
            await inp.delete()
        except discord.Forbidden:
            pass
        return num % 360

    async def getImageFrom(ctx: BuilderContext, message: discord.Message):
        """
        Gets an Image object from a message. If it references a message, it uses that message instead
        """
        if not message.reference:
            return await ImageManipulateView._getAttachmentFrom(ctx, message)
        else:
            ctx.bot: Builder = ctx.bot
            message = await ctx.channel.fetch_message(message.reference.message_id)
            return await ImageManipulateView._getAttachmentFrom(ctx, message)

    async def _getAttachmentFrom(ctx: BuilderContext, message: discord.Message):
        """
        Gets an image object from a message, not taking into account message references.
        """
        regex = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        if not message.attachments:
            if not (match := regex.fullmatch(message.content)):
                raise ValueError("Cannot locate valid image.")
            else:
                response: aiohttp.ClientResponse = await ctx.bot.session.get(
                    match.string
                )
                img = await response.read()
                try:
                    return wimage.Image(blob=img)
                except BaseException:
                    raise ValueError("Could not load URL image.")
        else:
            file = message.attachments[0]
            buffer = BytesIO()
            try:
                await file.save(buffer)
            except discord.HTTPException:
                await ctx.reply(
                    "Sorry, I had a spasm and couldn't read that image. Please try again :("
                )
                return
            buffer.seek(0)

            try:
                return wimage.Image(blob=buffer)
            except BaseException:
                raise ValueError("Could not load attachment into image.")


async def setup(bot: Builder):
    await bot.add_cog(Images(bot))
