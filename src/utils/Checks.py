from typing import Callable
from discord.ext import commands
import re


def inter_choke(ctx: commands.Context):
    async def predicate():
        command = """
            SELECT commands
            FROM disabled_commands
            WHERE guildid = $1
        """
        result = await ctx.bot.apg.fetchrow(command, ctx.guild.id)
        print(result)
        if ctx.command.qualified_name in result:
            return False
        return True

    return commands.check(predicate)


def control_defer(defer: bool = True, thinking: bool = True, ephemeral: bool = False):
    def deco(func: Callable):
        func.defer = {"defer": defer, "thinking": thinking, "ephemeral": ephemeral}
        return func

    return deco


def is_valid_url(s: str):
    regex = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    return regex.match(s) is not None
