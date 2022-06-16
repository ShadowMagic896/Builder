import asyncio
from typing import Any, Callable, Coroutine, Mapping
from discord.ext import commands


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
