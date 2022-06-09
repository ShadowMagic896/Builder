from typing import Literal, Optional
from discord.ext import commands
from discord.app_commands import Range, describe

from src.utils.Converters import RGB, ColorChannelConverterAlpha
from src.utils.ColorFuncs import filter_channels, merge
from src.utils.Embeds import fmte
from src.cogs.main.Images import PILFN

from PIL import Image


class Colors(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.hybrid_group()
    async def color(self, ctx: commands.Context):
        pass

    @color.command()
    @describe(
        color="The color to fill in",
        sizex="The X size of the image",
        sizey="The Y size of the image",
    )
    async def fill(
        self,
        ctx: commands.Context,
        color: RGB(alpha=False),
        sizex: Optional[Range[int, 2**4, 2**11]] = 512,
        sizey: Optional[Range[int, 2**4, 2**11]] = 512,
    ):
        """
        Fills in a blank image with one color
        """
        image = Image.new("P", color=tuple(color), size=(sizex, sizey))
        embed = fmte(ctx, t=f"Showing Color: {color}")
        embed, file = await PILFN.spawnItems(embed, image)
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
        ctx: commands.Context,
        color1: RGB(alpha=False),
        color2: RGB(alpha=False),
        channel: Literal["R", "G", "B", "RG", "RB", "GB", "RGB"] = "RGB",
        sizex: Optional[Range[int, 2**4, 2**11]] = 512,
        sizey: Optional[Range[int, 2**4, 2**11]] = 512,
    ):
        """
        Merges two colors together, then shows it
        """
        result = merge(color1, color2, channel)
        image = Image.new("P", color=tuple(result), size=(sizex, sizey))
        embed = fmte(ctx, t=f"Showing Merged Colors: {color1} & {color2}")
        embed.add_field(name="Channels:", value=channel)
        embed.add_field(name="Merging Result:", value=result)
        embed, file = await PILFN.spawnItems(embed, image)
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
        ctx: commands.Context,
        color: RGB(alpha=False),
        channel: ColorChannelConverterAlpha,
        sizex: Optional[Range[int, 2**4, 2**11]] = 512,
        sizey: Optional[Range[int, 2**4, 2**11]] = 512,
    ):
        """
        Merges two colors together, then shows it
        """
        result = filter_channels(color, 255 - color, channel)
        image = Image.new("P", color=tuple(result), size=(sizex, sizey))
        embed = fmte(ctx, t=f"Showing Inverted Color: {color}")
        embed.add_field(name="Channels:", value=channel)
        embed.add_field(name="Inverting Result:", value=result)
        embed, file = await PILFN.spawnItems(embed, image)
        await ctx.send(embed=embed, file=file)


async def setup(bot: commands.Bot):
    await bot.add_cog(Colors(bot))
