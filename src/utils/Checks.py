"""
Contains all command checks that the bot uses
"""

from discord.ext import commands


def interactionChoke(ctx: commands.Context):
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
