import sys
import traceback
from typing import Any, Union
import discord
from discord.ext import commands
from discord.ext.commands.errors import *
from discord.errors import *

from src.utils.errors import (
    InternalError,
    MissingArguments,
    MissingFunds,
    MissingShopEntry,
    SelfAction,
    Unowned,
)
from data.settings import (
    CATCH_ERRORS,
    MODERATE_JISHAKU_COMMANDS,
    PRINT_COMMAND_ERROR_TRACKEBACK,
    PRINT_EVENT_ERROR_TRACEACK,
)

from src.utils.embeds import fmte_i
from simpleeval import NumberTooHigh

from bot import BuilderContext


class ErrorHandling(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        print("Load error handler")
        self.bot = bot
        if CATCH_ERRORS:
            print("Setting attrs")
            self.bot.on_error = self.on_error
            self.bot.on_command_error = self.on_command_error
            self.bot.tree.on_error = self.on_tree_error

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        if PRINT_EVENT_ERROR_TRACEACK:
            sys.stderr.write(f"[EVENT ERROR]\n{event_method} with {args}, {kwargs}")
            traceback.print_exc(file=sys.stderr)

    async def on_command_error(self, ctx: BuilderContext, error: Exception):
        if PRINT_COMMAND_ERROR_TRACKEBACK:
            sys.stderr.write(
                f"[COMMAND ERROR]\n{ctx.command.qualified_name} with {ctx.args}"
            )
            traceback.print_tb(error.__traceback__, file=sys.stderr)
        return await self._interaction_error_handler(ctx.interaction, error)

    async def on_tree_error(self, interaction: discord.Interaction, error: Exception):
        return await self._interaction_error_handler(interaction, error)

    async def _interaction_error_handler(
        self, inter: discord.Interaction, error: Exception = None
    ):
        print("CATCH ERROR")
        if error is None:
            inter, error = self, inter
        if not CATCH_ERRORS:
            raise error
        if not MODERATE_JISHAKU_COMMANDS and "jishaku" in str(error):
            raise error

        while isinstance(
            error,
            Union[
                commands.errors.CommandInvokeError,
                discord.app_commands.errors.CommandInvokeError,
                commands.errors.HybridCommandError,
            ],
        ):
            error = error.original

        errorDir = {
            CommandNotFound: "I couldn't find that command. Try `/help`",
            ExtensionNotFound: "I couldn't find that cog. Try `/help`",
            NotFound: "I couldn't find that. Try `/help`, or check the error for more info.",
            Forbidden: "I'm not allowed to do that.",
            MissingRequiredArgument: "You need to supply more information to use that command.",
            NSFWChannelRequired: "You must be in an NSFW channel to use that.",
            UserNotFound: "That user was not found in discord.",
            MemberNotFound: "That member was not found in this server.",
            BadArgument: "You passed an invalid option.",
            TimeoutError: "This has timed out. Next time, try to be quicker.",
            CommandOnCooldown: "Slow down! You can't use that right now.",
            ValueError: "You gave something of the wrong value or type. Check the error for more information.",
            TypeError: "You gave something of the wrong value or type. Check the error for more information.",
            IOError: "You gave an incorrect parameter for a file.",
            NumberTooHigh: "Your number is too big for me to compute.",
            InternalError: "An internal error occurred.",
            Unowned: "You do not own this, so you can't interact with it.",
            MissingFunds: "You don't have enough money for this",
            MissingShopEntry: "I cannot find this shop.",
            SelfAction: "You cannot do this to something you own.",
            MissingArguments: "You didn't input enough arguments.",
            TooManyArguments: "You gave too many arguments.",
        }

        default: str = (
            "An unknown error has occurred. Please use `/bug` to report this."
        )
        hint: str = errorDir.get(type(error), default)

        embed = fmte_i(
            inter,
            t=hint,
            d=f"**Error:**\n`{error}`",
            c=discord.Color.red(),
        )
        try:
            await inter.response.send_message(embed=embed, ephemeral=True)
        except InteractionResponded:
            await inter.followup.send(embed=embed, ephemeral=True)

    async def handle_modal_error(interaction: discord.Interaction, error: Exception):
        return await ErrorHandling._interaction_error_handler(interaction, error)


async def setup(bot):
    await bot.add_cog(ErrorHandling(bot))
