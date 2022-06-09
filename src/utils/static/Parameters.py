import itertools
from typing import Literal
import discord
from discord.ext import commands
from discord.ext.commands import parameter
from src.utils import Converters


class Parameters:
    USER = parameter(
        default=lambda c: c.author, displayed_default=lambda c: str(c.author)
    )
    COLOR_CHANNEL_ALPHA = parameter(
        converter=Converters.ColorChannelConverterAlpha,
        default=lambda c: "RGB",
        displayed_default=lambda c: "RGB",
    )
    COLOR_CHANNEL_NO_ALPHA = parameter(
        converter=Converters.ColorChannelConverterNoAlpha,
        default=lambda c: "RGB",
        displayed_default=lambda c: "RGB",
    )


class TypeHints:
    USER = discord.User
    MEMBER = discord.Member
    COLOR_CHANNEL_ALPHA = Literal[
        "R",
        "G",
        "B",
        "A",
        "RG",
        "RB",
        "RA",
        "GB",
        "GA",
        "BA",
        "RGB",
        "RGA",
        "RBA",
        "GBA",
        "RGBA",
    ]
    COLOR_CHANNEL_NO_ALPHA = Literal["R", "G", "B", "RG", "RB", "GB", "RGB"]
