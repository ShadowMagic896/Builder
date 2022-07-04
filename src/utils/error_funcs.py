import sys

import discord
import traceback
from discord.ext import commands
from discord.ext.commands import errors as de
from settings import (
    CATCH_ERRORS,
    MODERATE_JISHAKU_COMMANDS,
    PRINT_COMMAND_ERROR_TRACKEBACK,
    PRINT_EVENT_ERROR_TRACEACK,
)
from simpleeval import NumberTooHigh
from typing import Any, Optional, Union

from . import errors as be
from .bot_types import BuilderContext
from .embeds import format


async def on_error(event_method: str, /, *args: Any, **kwargs: Any) -> None:
    print("on_error")
    if PRINT_EVENT_ERROR_TRACEACK:
        sys.stderr.write(f"[EVENT ERROR]\n{event_method} with {args}, {kwargs}")
        traceback.print_exc(file=sys.stderr)


async def on_command_error(ctx: commands.Context, error: Exception):
    print("on_command_error")
    if PRINT_COMMAND_ERROR_TRACKEBACK:
        sys.stderr.write(
            f"[COMMAND ERROR]\n{ctx.command.qualified_name} with {ctx.args}"
        )
        traceback.print_tb(error.__traceback__, file=sys.stderr)
    return await _interaction_error_handler(ctx.interaction, error)


async def on_tree_error(interaction: discord.Interaction, error: Exception):
    print("on_tree_error")
    return await _interaction_error_handler(interaction, error)


async def _interaction_error_handler(
    inter: discord.Interaction, error: Exception = None
):
    print("_interaction_error_handler")
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

    err_dir = {
        ValueError: "You gave something of the wrong value or type. Check the error for more information",
        TypeError: "You gave something of the wrong value or type. Check the error for more information",
        IOError: "You gave an incorrect parameter for a file",
        TimeoutError: "This has timed out. Next time, try to be quicker",
        NumberTooHigh: "Your number is too big for me to compute",
        
        de.BadArgument: "You passed an invalid option",
        de.CommandNotFound: "I couldn't find that command. Try `/help`",
        de.CommandOnCooldown: "Slow down! You can't use that right now",
        de.ExtensionNotFound: "I couldn't find that cog. Try `/help`",
        de.MemberNotFound: "That member was not found in this server",
        de.MissingRequiredArgument: "You need to supply more information to use that command",
        de.NSFWChannelRequired: "You must be in an NSFW channel to use that",
        de.UserNotFound: "That user was not found in discord",

        discord.Forbidden: "I'm not allowed to do that",
        discord.NotFound: "I couldn't find that. Try `/help`, or check the error for more info",

        be.ContainerAlreadyRunning: "You are already running a container",
        be.Fatal: "A fatal error has occurred. Ouch",
        be.ForbiddenData: "You cannot access this data",
        be.InternalError: "An internal error occurred",
        be.MissingArguments: "You didn't input enough arguments",
        be.MissingCog: "Cannot find that Cog",
        be.MissingGroup: "Cannot find that Group",
        be.MissingCommand: "Cannot find that Command",
        be.MissingFunds: "You don't have enough money for this",
        be.MissingShopEntry: "I cannot find this shop",
        be.NoDocumentsFound: "Cannot find anything with those parameters",
        be.ScopeError: "You cannot use that command here",
        be.SelfAction: "You cannot do this to something you own",
        be.SessionInProgress: "You are already running an eval session",
        be.TooManyArguments: "You gave too many arguments",
        be.Unowned: "You do not own this, so you can't interact with it",
    }

    default: str = "An unknown error has occurred. Please use `/bug` to report this"
    hint: str = err_dir.get(type(error), default)

    embed = await format(
        commands.Context.from_interaction(inter),
        title=hint,
        desc=f"**Error:**\n`{error}`",
        color=discord.Color.red(),
    )
    try:
        await inter.response.send_message(embed=embed, ephemeral=True)
    except discord.InteractionResponded:
        await inter.followup.send(embed=embed, ephemeral=True)


async def handle_modal_error(interaction: discord.Interaction, error: Exception):
    return await _interaction_error_handler(interaction, error)


class GetCogHelp(discord.ui.View):
    def __init__(self, ctx: BuilderContext, command: commands.Command, error_embed: discord.Embed, timeout: Optional[float] = 900):
        self.embed = error_embed
        self.command = command
        super().__init__(ctx, timeout)
    
    @discord.ui.button(label="View Help", style=discord.ButtonStyle.blurple,)
    async def view_help(self, inter: discord.Interaction, button: discord.ui.Button):
        cog = self.ctx.bot.cogs["Help"]
        ext = self.ctx.bot.extensions["help"]
        embed = await cog.command_embed(self.ctx, self.command)
        view = await ext.CommandView(self.ctx, self.command.cog)

        await inter.response.edit_message(embeds=[embed, self.embed], view=view)
