import math

import discord
import io
import numpy as np
import simpleeval
from copy import copy
from discord.app_commands import Range, describe
from discord.ext import commands
from matplotlib import pyplot as plt
from typing import Callable, Literal, Optional, Union

from ..utils.bot_types import Builder, BuilderContext
from ..utils.converters import ListConverter

from ..utils.subclass import BaseCog


class Graphing(BaseCog):
    """
    Commands for visualizing data and functions
    """

    def ge(self):
        return "\U0001f4ca"

    def color_autocomplete(self, inter, current: str):
        colors = [
            "aqua",
            "aquamarine",
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
            "yellowgreen",
        ]
        return [
            discord.app_commands.Choice(name=c, value=c)
            for c in colors
            if c in current or current in c
        ][:25]

    @commands.hybrid_group()
    async def graph(self, ctx: BuilderContext):
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
        ctx: BuilderContext,
        xvalues: ListConverter(float),
        yvalues: ListConverter(float),
        xlabel: str = "X Axis",
        ylabel: str = "Y Axis",
        title: Optional[str] = None,
        color: str = "black",
        linewidth: Range[float, 0.1, 100.0] = 5.0,
        font: Literal[
            "serif", "sans-serif", "cursive", "fantasy", "monospace"
        ] = "monospace",
        xticks: Range[int, 0, 30] = 10,
        yticks: Range[int, 0, 30] = 10,
    ):
        """
        Graphs X-Values and Y-Values on a line plot using matplotlib and shows the result
        """
        if len(xvalues) != len(yvalues):
            raise commands.errors.BadArgument(
                "Values have uneven amounts of data [{} vs {}]".format(
                    len(xvalues), len(yvalues)
                )
            )
        buffer = io.BytesIO()

        plt.plot(xvalues, yvalues, color=color, linewidth=linewidth)
        plt.grid(True)

        plt.title(title if title else str(ctx.author))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        xmin, xmax, ymin, ymax = (
            min(xvalues),
            max(xvalues),
            min(yvalues),
            max(yvalues),
        )
        plt.xticks(np.linspace(xmin, xmax, xticks))
        plt.yticks(np.linspace(ymin, ymax, yticks))

        plt.minorticks_on()
        plt.rcParams.update({"font.family": font})

        plt.savefig(buffer)

        buffer.seek(0)
        embed = await ctx.format(title="Data Loaded and Graphed")
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
        ctx: BuilderContext,
        xvalues: ListConverter(str),
        yvalues: ListConverter(float),
        xlabel: str = "X Axis",
        ylabel: str = "Y Axis",
        title: Optional[str] = None,
        color: str = "black",
        barwidth: Range[float, 0.1, 100.0] = 5.0,
        font: Literal[
            "serif", "sans-serif", "cursive", "fantasy", "monospace"
        ] = "monospace",
        yticks: Range[int, 0, 30] = 10,
    ):
        """
        Graphs X-Values and Y-Values on a bar graph using matplotlib and shows the result
        """
        if len(xvalues) != len(yvalues):
            raise commands.errors.BadArgument(
                "Values have uneven amounts of data [{} vs {}]".format(
                    len(xvalues), len(yvalues)
                )
            )
        buffer = io.BytesIO()

        plt.bar(xvalues, yvalues, color=color, linewidth=barwidth)
        plt.grid(True)

        plt.title(title if title else str(ctx.author))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        ymin, ymax = (
            min(yvalues),
            max(yvalues),
        )
        plt.yticks(np.linspace(ymin, ymax, yticks))

        plt.minorticks_on()
        plt.rcParams.update({"font.family": font})

        plt.savefig(buffer)

        buffer.seek(0)
        embed = await ctx.format(title="Data Loaded and Graphed")
        file = discord.File(buffer, filename="graph.png")
        await ctx.send(embed=embed, file=file)
        plt.cla()

    @bar.autocomplete("color")
    async def barcolor_autocomplete(self, inter: discord.Interaction, current: str):
        return self.color_autocomplete(inter, current)

    @graph.command()
    @describe(
        function="The functiont to graph, in slope-intercept form.",
        start="Where to start graphing Y. Inclusive",
        stop="Where to stop graphing Y. Exclusive",
        step="how many plots of Y to make.",
        xlabel="The label of the graph's X axis.",
        ylabel="The label of the graph's Y axis.",
        title="The title of the graph",
        color="The color of the line.",
        linewidth="Width of the line. If left empty, it will be decided automatically.",
        font="The font of the text for the labels and title.",
    )
    async def psi(
        self,
        ctx: BuilderContext,
        function: str,
        start: int,
        stop: int,
        step: int = 1,
        xlabel: str = "X Axis",
        ylabel: str = "Y Axis",
        title: Optional[str] = None,
        color: str = "blue",
        linewidth: Range[float, 0.1, 100.0] = 2.5,
        font: Literal[
            "serif", "sans-serif", "cursive", "fantasy", "monospace"
        ] = "monospace",
    ):
        """
        Graphs Y using a function in slope-intercept form (y = mx + b)
        """
        clamp: Callable[[Union[float, int], Optional[int], Optional[int]]] = (
            lambda n, l=None, m=None: min(max(n, l), m)
            if m is not None and l is not None
            else max(n, l)
            if m is None
            else min(n, m)
            if l is None
            else n
        )
        start, stop = clamp(start, l=stop - 200, m=stop - 1), clamp(
            stop, l=start + 1, m=start + 200
        )
        ofunc = copy(function)
        buffer = io.BytesIO()
        xvalues = list(range(round(start), round(stop), round(step)))
        yvalues = []
        function = function.replace(" ", "").replace("y=", "")

        def ins(string: str, char: str, pos: int):
            return string[:pos] + char + string[pos:]

        for co, char in enumerate(function):
            if co == 0:
                continue
            if char == "x":
                if function[co - 1].isdigit():
                    function = ins(function, "*", co)

        evaluator = simpleeval.SimpleEval(
            functions=self.functions(),
            names=self.names(),
        )

        for v in xvalues:
            n_function = function.replace("x", str(v))
            result = evaluator.eval(n_function)
            yvalues.append(result)

        fig, ax = plt.subplots()
        plt.plot(xvalues, yvalues, color=color, linewidth=linewidth)
        plt.grid(True)

        plt.title(f"{title or ofunc}")
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        plt.xticks(xvalues)

        plt.minorticks_on()
        plt.rcParams.update({"font.family": font})
        [
            ax.text(
                xvalues[index],
                yvalues[index],
                round(yvalues[index], 4),
                fontsize=10,
                horizontalalignment="center",
            )
            for index in range(len(xvalues))
        ]

        with np.errstate(divide="ignore"):
            plt.savefig(buffer)

        buffer.seek(0)
        embed = await ctx.format(title="Data Loaded and Graphed")
        file = discord.File(buffer, filename="graph.png")
        await ctx.send(embed=embed, file=file)
        plt.cla()

    @psi.autocomplete("color")
    async def psicolor_autocomplete(self, inter: discord.Interaction, current: str):
        return self.color_autocomplete(inter, current)

    def functions(self):
        dft = simpleeval.DEFAULT_FUNCTIONS
        dft.update(
            {
                "acos": math.acos,
                "acosh": math.acosh,
                "asin": math.asin,
                "asinh": math.asinh,
                "atan": math.atan,
                "atan2": math.atan2,
                "atanh": math.atanh,
                "ceil": math.ceil,
                "comb": math.comb,
                "copysign": math.copysign,
                "cos": math.cos,
                "cosh": math.cosh,
                "degrees": math.degrees,
                "dist": math.dist,
                "erf": math.erf,
                "erfc": math.erfc,
                "exp": math.exp,
                "expm1": math.expm1,
                "fabs": math.fabs,
                "factorial": math.factorial,
                "floor": math.floor,
                "fmod": math.fmod,
                "frexp": math.frexp,
                "fsum": math.fsum,
                "gamma": math.gamma,
                "gcd": math.gcd,
                "hypot": math.hypot,
                "inf": math.inf,
                "isclose": math.isclose,
                "isfinite": math.isfinite,
                "isinf": math.isinf,
                "isnan": math.isnan,
                "isqrt": math.isqrt,
                "ldexp": math.ldexp,
                "lgamma": math.lgamma,
                "log": math.log,
                "log10": math.log10,
                "log1p": math.log1p,
                "log2": math.log2,
                "modf": math.modf,
                "perm": math.perm,
                "pow": math.pow,
                "prod": math.prod,
                "radians": math.radians,
                "remainder": math.remainder,
                "sin": math.sin,
                "sinh": math.sinh,
                "sqrt": math.sqrt,
                "round": round,
                "range": range,
            }
        )
        return dft

    def names(self):
        dft = simpleeval.DEFAULT_NAMES
        dft.update(
            {
                "pi": math.pi,
                "e": math.e,
            }
        )
        return dft


async def setup(bot):
    await bot.add_cog(Graphing(bot))
