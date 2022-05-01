import discord
from discord.app_commands import describe, Range
from discord.ext import commands

from _aux.embeds import fmte
from _aux.userio import explode
from _aux.Converters import ListConverter

import io
import simpleeval
import numpy as np
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
        ylabel: str = "Y Axis",

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
            raise commands.errors.BadArgument(
                "Values have uneven amounts of data [{} vs {}]".format(
                    len(xvalues), len(yvalues)))
        buffer = io.BytesIO()

        plt.plot(xvalues, yvalues, color=color, linewidth=linewidth)
        plt.grid(True)

        plt.title(title if title else str(ctx.author))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        xmin, xmax, ymin, ymax = min(xvalues), max(
            xvalues), min(yvalues), max(yvalues),
        plt.xticks(
            np.linspace(xmin, xmax, xticks)
        )
        plt.yticks(
            np.linspace(ymin, ymax, yticks)
        )

        plt.minorticks_on()
        plt.rcParams.update({"font.family": font})

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
    @describe(
        xvalues="An array of strings, seperated by a comma. Example: Group 1, Group 2",
        yvalues="An array of numbers, seperated by a comma. Example: 13.5, -13.102",
        xlabel="The label of the graph's X axis.",
        ylabel="The label of the graph's Y axis.",
        title="The title of the graph",
        color="The color of the line.",
        barwidth="Width of the bars. If left empty, it will be decided automatically.",
        font="The font of the text for the labels and title.",
        yticks="The amount of ticks on the Y Axis.",
    )
    async def bar(
        self,
        ctx: commands.Context,

        xvalues: ListConverter(str),
        yvalues: ListConverter(float),

        xlabel: str = "X Axis",
        ylabel: str = "Y Axis",

        title: Optional[str] = None,
        color: str = "black",

        barwidth: Range[float, 0.1, 100.0] = 5.0,
        font: Literal["serif", "sans-serif", "cursive", "fantasy", "monospace"] = "monospace",

        yticks: Range[int, 0, 30] = 10,
    ):
        """
        Graphs X-Values and Y-Values on a bar graph using matplotlib and shows the result
        """
        if len(xvalues) != len(yvalues):
            raise commands.errors.BadArgument(
                "Values have uneven amounts of data [{} vs {}]".format(
                    len(xvalues), len(yvalues)))
        buffer = io.BytesIO()

        plt.bar(xvalues, yvalues, color=color, linewidth=barwidth)
        plt.grid(True)

        plt.title(title if title else str(ctx.author))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        ymin, ymax = min(yvalues), max(yvalues),
        plt.yticks(
            np.linspace(ymin, ymax, yticks)
        )

        plt.minorticks_on()
        plt.rcParams.update({"font.family": font})

        plt.savefig(buffer)

        buffer.seek(0)
        embed = fmte(
            ctx,
            t="Data Loaded and Graphed"
        )
        file = discord.File(buffer, filename="graph.png")
        await ctx.send(embed=embed, file=file)
        plt.cla()

    @bar.autocomplete("color")
    async def barcolor_autocomplete(self, inter: discord.Interaction, current: str):
        return self.color_autocomplete(inter, current)

    @graph.command()
    @describe(function="The functiont to graph, in slope-intercept form.",
              rangelower="Where to start graphing Y.",
              rangeupper="Where to stop graphing Y.",
              plots="how many plots of Y to make.",
              xlabel="The label of the graph's X axis.",
              ylabel="The label of the graph's Y axis.",
              title="The title of the graph",
              color="The color of the line.",
              linewidth="Width of the line. If left empty, it will be decided automatically.",
              font="The font of the text for the labels and title.",
              xticks="How many ticks to place on the X axis.",
              yticks="How many ticks to place on the Y axis.",
              )
    async def psi(
        self,
        ctx: commands.Context,

        function: str,
        rangelower: float,
        rangeupper: float,
        plots: int = 50,

        xlabel: str = "X Axis",
        ylabel: str = "Y Axis",

        title: Optional[str] = None,
        color: str = "black",

        linewidth: Range[float, 0.1, 100.0] = 5.0,
        font: Literal["serif", "sans-serif", "cursive",
                      "fantasy", "monospace"] = "monospace",

        xticks: Range[int, 0, 30] = 10,
        yticks: Range[int, 0, 30] = 10,
        # autoperspective: bool = False
    ):
        """
        Graphs Y using a function in slope-intercept form (y = mx + b)
        """
        buffer = io.BytesIO()
        xvalues = np.linspace(rangelower, rangeupper, plots)
        yvalues = []
        function = function.replace(" ", "").replace(
            "^", "**").replace("y=", "")
        if function.count("x"):
            if function.index("x") == 0:
                ast = False
            else:
                ast = function[function.index("x") - 1].isdigit
        for v in xvalues:
            yvalues.append(
                simpleeval.SimpleEval().eval(
                    function.replace(
                        "x", ("*%s" %
                              v) if ast else str(v))))
        plt.plot(xvalues, yvalues, color=color, linewidth=linewidth)
        plt.grid(True)

        plt.title(title if title else str(ctx.author))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        xmax, ymax = max(
            xvalues), max(yvalues),

        plt.xticks(
            np.linspace(0, xmax, xticks)
        )
        plt.yticks(
            np.linspace(0, ymax, yticks)
        )

        plt.minorticks_on()
        plt.rcParams.update({"font.family": font})

        plt.savefig(buffer)

        buffer.seek(0)
        embed = fmte(
            ctx,
            t="Data Loaded and Graphed"
        )
        file = discord.File(buffer, filename="graph.png")
        print("SEnd")
        await ctx.send(embed=embed, file=file)
        plt.cla()

    @psi.autocomplete("color")
    async def psicolor_autocomplete(self, inter: discord.Interaction, current: str):
        return self.color_autocomplete(inter, current)


async def setup(bot):
    await bot.add_cog(Graphing(bot))
