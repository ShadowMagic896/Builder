from math import ceil, floor
import discord
from discord.app_commands import describe, Range, guilds
from discord.ext import commands
import numpy as np
from pyparsing import line

from _aux.embeds import fmte
from _aux.Converters import ListConverter

import io
from typing import Literal, Optional
from matplotlib import pyplot as plt


class Graphing(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def ge(self):
        return "📊"

    
    def color_autocomplete(self, inter, current: str):
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
        linewidth="Width of the line. If left empty, it will be decided automatically.",
        font="The font of the text for the labels and title.",
        xticks="The amount of ticks on the X Axis.",
        yticks="The amount of ticks on the Y Axis.",
    )
    async def plot(
        self,
        ctx: commands.Context,

        xvalues: ListConverter(float),
        yvalues: ListConverter(float),

        xlabel: str = "X Axis",
        ylabel: str = "X Axis",

        title: Optional[str] = None,
        color: str = "black",

        linewidth: Range[float, 0.1, 100.0] = 5.0,
        font: Literal["serif", "sans-serif", "cursive", "fantasy", "monospace"] = "monospace",

        xticks: Range[int, 0, 30] = 10,
        yticks: Range[int, 0, 30] = 10,
    ):
        """
        Graphs X-Values and Y-Values on a line plot using matplotlib and shows the result
        """
        if len(xvalues) != len(yvalues):
            raise commands.errors.BadArgument("Values have uneven amounts of data [{} vs {}]".format(len(xvalues), len(yvalues)))
        buffer = io.BytesIO()

        plt.plot(xvalues, yvalues, color=color, linewidth=linewidth)
        plt.grid(True)

        plt.title(title if title else str(ctx.author))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        xmin, xmax, ymin, ymax = min(xvalues), max(xvalues), min(yvalues), max(yvalues),
        plt.xticks(
            np.arange(xmin, xmax, (xmax - xmin) / xticks)
        )
        plt.yticks(
            np.arange(ymin, ymax, (ymax - ymin) / yticks)
        )


        plt.minorticks_on()
        plt.rcParams.update({"font.family":font})

        plt.savefig(buffer)

        buffer.seek(0)
        embed = fmte(
            ctx,
            t="Data Loaded and Graphed"
        )
        file = discord.File(buffer, filename="graph.png")
        await ctx.send(embed=embed, file=file)
        plt.cla()

    @plot.autocomplete("color")
    async def plotcolor_autocomplete(self, inter: discord.Interaction, current: str):
        return self.color_autocomplete(inter, current)
    
    @graph.command()
    async def bar(
        self,
        ctx: commands.Context,

        xvalues: ListConverter(str),
        yvalues: ListConverter(float),

        xlabel: str = "X Axis",
        ylabel: str = "X Axis",

        title: Optional[str] = None,
        color: str = "black",

        linewidth: Range[float, 0.1, 100.0] = 5.0,
        font: Literal["serif", "sans-serif", "cursive", "fantasy", "monospace"] = "monospace",

        xticks: Range[int, 0, 30] = 10,
        yticks: Range[int, 0, 30] = 10,
    ):
        """
        Graphs X-Values and Y-Values on a line plot using matplotlib and shows the result
        """
        if len(xvalues) != len(yvalues):
            raise commands.errors.BadArgument("Values have uneven amounts of data [{} vs {}]".format(len(xvalues), len(yvalues)))
        buffer = io.BytesIO()

        plt.bar(xvalues, yvalues, color=color, linewidth=linewidth)
        plt.grid(True)

        plt.title(title if title else str(ctx.author))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        xmin, xmax, ymin, ymax = min(xvalues), max(xvalues), min(yvalues), max(yvalues),
        plt.xticks(
            np.arange(xmin, xmax, (xmax - xmin) / xticks)
        )
        plt.yticks(
            np.arange(ymin, ymax, (ymax - ymin) / yticks)
        )


        plt.minorticks_on()
        plt.rcParams.update({"font.family":font})

        plt.savefig(buffer)

        buffer.seek(0)
        embed = fmte(
            ctx,
            t="Data Loaded and Graphed"
        )
        file = discord.File(buffer, filename="graph.png")
        await ctx.send(embed=embed, file=file)
        plt.cla()

async def setup(bot):
    await bot.add_cog(Graphing(bot))
