from copy import copy
from typing import Optional

from discord.app_commands import Range, describe
from discord.ext import commands
from PIL import Image

from src.cogs.images import PILFN

from ..utils.abc import BaseCog
from ..utils.bot_abc import Builder, BuilderContext
from ..utils.colors import channels_to_names, merge
from ..utils.converters import RGB
from ..utils.static.parameters import COLOR_CHANNEL_ALPHA


class Colors(BaseCog):
    """
    Manipulate RGB colors
    """

    def ge(self):
        return "\N{Artist Palette}"

    @commands.hybrid_group()
    async def color(self, ctx: BuilderContext):
        pass

    @color.command()
    @describe(
        color="The color to fill in",
        sizex="The X size of the image",
        sizey="The Y size of the image",
    )
    async def fill(
        self,
        ctx: BuilderContext,
        color: RGB(),
        sizex: Optional[Range[int, 2**4, 2**11]] = 512,
        sizey: Optional[Range[int, 2**4, 2**11]] = 512,
    ):
        """
        Fills in a blank image with one color
        """
        image = Image.new("RGBA", color=tuple(color), size=(sizex, sizey))
        embed = await ctx.format(title=f"Showing Color: {color}")
        embed, file = await PILFN.local_embed(embed, image)
        await ctx.send(embed=embed, file=file)

    @color.command()
    @describe(
        color1="The first color to merge",
        color2="The second color to merge",
        channel="The RGB channels to merge",
        sizex="The X size of the image",
        sizey="The Y size of the image",
    )
    async def merge(
        self,
        ctx: BuilderContext,
        color1: RGB(),
        color2: RGB(),
        channel=COLOR_CHANNEL_ALPHA,
        sizex: Optional[Range[int, 2**4, 2**11]] = 512,
        sizey: Optional[Range[int, 2**4, 2**11]] = 512,
    ):
        """
        Merges two colors together, then shows it
        """
        result = merge(color1, color2, channel)
        image = Image.new("RGBA", color=tuple(result), size=(sizex, sizey))
        embed = await ctx.format(title=f"Showing Merged Colors: {color1} & {color2}")
        embed.add_field(name="Channels:", value=channels_to_names(channel))
        embed.add_field(name="Merging Result:", value=result)
        embed, file = await PILFN.local_embed(embed, image)
        await ctx.send(embed=embed, file=file)

    @color.command()
    @describe(
        color="The color to invert",
        channel="The RGB channels to invert",
        sizex="The X size of the image",
        sizey="The Y size of the image",
    )
    async def invert(
        self,
        ctx: BuilderContext,
        color: RGB(),
        channel=COLOR_CHANNEL_ALPHA,
        sizex: Optional[Range[int, 2**4, 2**11]] = 512,
        sizey: Optional[Range[int, 2**4, 2**11]] = 512,
    ):
        """
        Merges two colors together, then shows it
        """
        original = copy(color)
        for chan in channel:
            color[chan] = 255 - color[chan]
        image = Image.new("RGBA", color=tuple(color), size=(sizex, sizey))
        embed = await ctx.format(title=f"Showing Inverted Color: {original}")
        embed.add_field(name="Channels:", value=channels_to_names(channel))
        embed.add_field(name="Inverting Result:", value=color)
        embed, file = await PILFN.local_embed(embed, image)
        await ctx.send(embed=embed, file=file)


async def setup(bot: Builder):
    await bot.add_cog(Colors(bot))
