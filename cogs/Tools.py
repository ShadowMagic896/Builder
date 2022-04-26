import imp
from math import ceil, floor, log2
from black import err
import discord
from discord.app_commands import describe
from discord.ext import commands

import os
from PIL import Image
from typing import Literal, Optional

from _aux.embeds import fmte

class Tools(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
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
        
        errored = [c for c in [width, height] if c < 32 or c > 2048 or ceil(log2(c)) != floor(log2(c))]
        if errored:
            raise commands.errors.BadArgument("Dimensions too large or not powers of 2: %s" % ", ".join(errored))

        ogsize = (attachment.width, attachment.height)

        fn = attachment.filename

        extension = fn[fn.replace(".", "_", fn.count(".")-1).index("."):]

        await attachment.save("data/PIL/resize%s%s" % (str(len(os.listdir("data/PIL"))), extension))

        filepath = "data/PIL/resize%s%s" % (str(len(os.listdir("data/PIL")) - 1), extension)

        img = Image.open(filepath)
        img = img.resize((width, height))

        img.save(filepath)

        embed = fmte(
            ctx,
            t = "Image successfully resized!",
            d = "File of dimensions (%s, %s) converted to file of dimensions (%s, %s)" %
            (ogsize[0], ogsize[1], width, height)
        )

        file = discord.File(filepath, filename="resize.%s" % fn)

        await ctx.send(embed=embed, file=file, ephemeral=ephemeral)
        os.remove(filepath)
    
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
        fn = attachment.filename
        extension = fn[fn.replace(".", "_", fn.count(".")-1).index("."):]
        if extension.lower() not in ["png", "jpg"]:
            raise TypeError("Only PNG and JPG files are permitted.")
        if attachment.size() > 8388608:
            raise IOError("Image size too large")
        await attachment.save("data/PIL/resize%s%s" % (str(len(os.listdir("data/PIL"))), extension))

        filepath = "data/PIL/resize%s%s" % (str(len(os.listdir("data/PIL")) - 1), extension)

        img = Image.open(filepath)
        img = img.resize((128, 128))

        img.save(filepath)
        buffer: bytes = open(filepath, "rb").read()

        e: discord.Emoji = await ctx.guild.create_custom_emoji(name=name, image=buffer, reason=reason)
        embed = fmte(
            ctx,
            t = "Emoji created!",
            d = "**Emoji:** %s\n**Name:** %s\n**Reason:** %s" %
            ("<:{}:{}>".format(e.name, e.id), e.name, reason)
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)
        os.remove(filepath)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tools(bot))