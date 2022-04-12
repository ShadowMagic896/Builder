import discord

from discord import Color as disco
from discord.ext import commands
from discord.ext.commands import when_mentioned_or


import os
import sys
import threading
import sqlite3
import json
import random
import time
import asyncio
import urllib
import math
from dotenv import load_dotenv

def fmte(ctx, t="", d="", c=disco.teal()) -> discord.Embed:
    embed=discord.Embed(
        title=t,
        description=d,
        color=c
    )
    embed.set_footer(text=f"Requested by {ctx.author}")
    return embed