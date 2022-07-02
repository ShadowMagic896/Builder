import discord
from typing import Literal


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
