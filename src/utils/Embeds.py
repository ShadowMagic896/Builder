import datetime
import discord
from typing import Optional, Union

from src.utils.bot_types import BuilderContext


async def getv(inter) -> Union[BuilderContext, None]:
    try:
        return await BuilderContext.from_interaction(inter)
    except ValueError:
        return None


async def format(
    ctx: BuilderContext, 
    title: Optional[str] = None,
    desc: Optional[str] = None,
    color: Optional[discord.Color] = discord.Color.teal()
    ):
    delay: str = f"{round(ctx.bot.latency, 3) * 1000}ms"
    author_name = str(ctx.author)
    author_url: str = f"https://discord.com/users/{ctx.author.id}"
    author_icon_url: str = ctx.author.display_avatar.url

    embed = discord.Embed(
        color=color,
        title=title,
        description=desc,
        type="rich",
        timestamp=datetime.datetime.now()
    )
    embed.set_author(
        name=author_name,
        url=author_url,
        icon_url=author_icon_url
    )

    embed.set_footer(
        text=f"{ctx.prefix}{ctx.command}  •  {delay}"
    )
        
    return embed


class Desc:
    user = "The target of this command."
    ephemeral = "Whether to publicly show the response to the command."
    reason = "The reason for using this command. Shows up in the server's audit log."
