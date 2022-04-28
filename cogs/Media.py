import asyncio
import io
import discord
from discord.app_commands import describe, Range
from discord.ext import commands

import os


from matplotlib import font_manager 
from PIL import Image, ImageDraw, ImageFont
from typing import Literal, Optional

from _aux.embeds import fmte

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
        return fn[fn.replace(".", "_", fn.count(".")-1).index("."):]
    
    def getFP(self, attachment: discord.Attachment):
        return "data/PIL/image%s%s" % (str(len(os.listdir("data/PIL"))), self.getExtension(attachment))
    
    def checkAttachment(self, attachment: discord.Attachment):
        if attachment.size > 40000000:
            raise IOError("Attachment is too large. Please keep files under 40MB")

    async def _resize(self, attachment: discord.Attachment, width, height) -> io.BytesIO:
        buffer = io.BytesIO()
        await attachment.save(buffer)

        img = Image.open(buffer)
        

        img = img.resize((width, height))
        img.save(buffer, "png")
        
        img.close() 
        
        buffer.seek(0)

        return buffer

    @commands.hybrid_command()
    @commands.cooldown(5, 60*60*3, commands.BucketType.user)
    @describe(
        width = "The new image's width.",
        height = "The new image's height.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def resize(self, ctx: commands.Context, attachment: discord.Attachment, width: int, height: int, ephemeral: bool = False):
        """
        Resizes an image to a certain width and height
        """
        self.checkAttachment(attachment)
        ogsize = (attachment.width, attachment.height)

        buffer = await self._resize(attachment, width, height)


        embed = fmte(
            ctx,
            t = "Image successfully resized!",
            d = "File of dimensions (%s, %s) converted to file of dimensions (%s, %s)" %
            (ogsize[0], ogsize[1], width, height)
        )

        file = discord.File(buffer, filename="resize.%s" % attachment.filename)
        await ctx.send(embed=embed, file=file, ephemeral=ephemeral)
    
    @commands.hybrid_command()
    @commands.cooldown(2, 60*60*3, commands.BucketType.user)
    @describe(
        name="What to name the new emoji.",
        reason="The reason for creating the emoji. Shows up in audit logs.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def steal(self, ctx: commands.Context, name: str, attachment: discord.Attachment, reason: Optional[str] = "No reason given", ephemeral: bool = False):
        """
        Copies an image attachment and adds it to the guild as an emoji
        """
        self.checkAttachment(attachment)
        extension = self.getExtension(attachment)

        if extension.lower() not in [".png", ".jpg"]:
            raise TypeError("Only PNG and JPG files are permitted. [Discord limitation]")
        
        fp = self.getFP(attachment)

        buffer = io.BytesIO()

        await attachment.save(buffer)

        img, filepath = await self._resize(attachment, 128, 128)

        buffer: bytes = open(filepath, "rb").read()

        e: discord.Emoji = await ctx.guild.create_custom_emoji(name=name, image=buffer, reason=reason)
        embed = fmte(
            ctx,
            t = "Emoji created!",
            d = "**Emoji:** %s\n**Name:** %s\n**Reason:** %s" %
            ("<:{}:{}>".format(e.name, e.id), e.name, reason)
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)
        img.close()
        os.remove(filepath)
    
    @commands.hybrid_command()
    @commands.cooldown(2, 60*60*3, commands.BucketType.user)
    @describe(
        text = "The text to add.",
        attachment = "The image to add the text to.",
        xpos = "The X-Position for the top-left corner of the text.",
        ypos = "The Y-Position for the top-left corner of the text.",
        direction = "The direction of the text. Right to left, Left to Right, or Top to Bottom.",
        align = "Where to align the text. Left, Center, or Right.",
        r = "The RED component of the text color.",
        g = "The GREEN component of the text color.",
        b = "The BLUE component of the text color.",
        ephemeral="Whether to publicly show the response to the command.",
    )
    async def text(
        self, 
        ctx: commands.Context, 
        text: str,
        attachment: discord.Attachment, 
        xpos: int, ypos: int,

        direction: Literal["rtl", "ltr", "ttb"] = "rtl",
        align: Literal["left", "center", "right"] = "left",

        font: str = "C:\\Windows\\Fonts\\PERTILI.TTF",
        strokeweight: Range[int, 1, 75] = 5,

        r: Range[int, 0, 255] = 255,
        g: Range[int, 0, 255] = 255,
        b: Range[int, 0, 255] = 255,

        ephemeral: bool = False
    ):
        """
        Adds text to an image. Does this have too many parameters? Yes.
        """
        fp = self.getFP(attachment)
        
        if font not in font_manager.findSystemFonts(fontpaths=None, fontext='ttf'):
            raise commands.errors.BadArgument("Invalid font given. Please use the autocomplete to find a font.")

        font = ImageFont.FreeTypeFont(font, size = strokeweight)

        buffer = io.BytesIO()
        
        await attachment.save(buffer)
        
        img = Image.open(buffer.read())
        drawer = ImageDraw.Draw(img)

        drawer.text((xpos, ypos), text, fill=(r, g, b), direction=direction, align=align)

        img.save(buffer)

        file = discord.File(buffer.read(), filename="text.%s" % attachment.filename)
        embed = fmte(
            ctx,
            t = "File Successfully Edited!"
        )
        await ctx.send(embed=embed, file=file, ephemeral=ephemeral)
        os.remove(fp)
    
    @text.autocomplete("font")
    async def font_autocomplete(self, inter: discord.Interaction, current: str):
        print("AHHHH")
        op = [
            discord.app_commands.Choice(name=c[20:-4], value=c)
            for c in font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
            if c[20:-4].lower() in current.lower() or current.lower() in c[20:-4].lower()
        ][:25]
        return op
    
    @commands.hybrid_command()
    async def avatar(self, ctx: commands.Context, user: Optional[discord.Member]):
        """
        Gets the avatar / profile picture of a member
        """
        user = user if user else ctx.author
        embed = fmte(
            ctx,
            t = "%s's Avatar" % user.display_name,
            d = "[View Link](%s)" % user.avatar.url
        )
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)

        


async def setup(bot: commands.Bot):
    await bot.add_cog(Media(bot))