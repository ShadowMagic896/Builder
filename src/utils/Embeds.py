import datetime
from typing import Optional, Union

import discord

from .bot_abc import BuilderContext


async def getv(inter) -> Union[BuilderContext, None]:
    try:
        return await BuilderContext.from_interaction(inter)
    except ValueError:
        return None


class Desc:
    user = "The target of this command."
    ephemeral = "Whether to publicly show the response to the command."
    reason = "The reason for using this command. Shows up in the server's audit log."
