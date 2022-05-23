from typing import Union
import discord
from discord.ext import commands
from discord.ext.commands.errors import *
from discord.errors import *

import asyncio
import time
from datetime import datetime
from data.errors import InternalError

from src.auxiliary.user.Embeds import fmte, fmte_i
from simpleeval import NumberTooHigh


class Watchers(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        print(error)
        hint = None

        if (
            "jishaku" in ctx.invoked_parents
        ):  # Do not automate command errors for this cog
            return

        while isinstance(
            error,
            Union[
                commands.errors.CommandInvokeError,
                discord.app_commands.errors.CommandInvokeError,
                commands.errors.HybridCommandError,
            ],
        ):
            error = error.original

        if isinstance(error, CommandNotFound):
            hint = "I couldn't find that command. Try `/help`"
        if isinstance(error, ExtensionNotFound):
            hint = "I couldn't find that cog. Try `/help`"
        elif isinstance(error, NotFound):
            hint = (
                "I couldn't find that. Try `/help`, or check the error for more info."
            )
        elif isinstance(error, Forbidden):
            hint = "I'm not allowed to do that."
        elif isinstance(error, MissingRequiredArgument):
            hint = "You need to supply more information to use that command. Try `/help [command]`"
        elif isinstance(error, NSFWChannelRequired):
            hint = "You must be in an NSFW channel to use that."
        elif isinstance(error, UserNotFound):
            hint = "That user was not found in discord."
        elif isinstance(error, MemberNotFound):
            hint = "That member was not found in this server."
        elif isinstance(error, BadArgument):
            hint = "You passed an invalid option."
        elif isinstance(error, asyncio.TimeoutError):
            hint = "This has timed out. Next time, try to be quicker."
        elif isinstance(error, CommandOnCooldown):
            hint = "Slow down! You can't use that right now."
        elif isinstance(error, ValueError) or isinstance(error, TypeError):
            hint = "You gave something of the wrong value or type. Check the error for more information."
        elif isinstance(error, IOError):
            hint = "You gave an incorrect parameter for a file."
        elif isinstance(error, NumberTooHigh):
            hint = "Your number is too big for me to compute."
        else:
            hint = "I'm not sure what went wrong, probably an internal error. Please contact `Cookie?#9461` with information on how to replicate the error you just recieved."
        hintEmbed = fmte(
            ctx,
            t="An Error Occurred.",
            d="**Hint:**\n{}\n**Error:**\n`{}`".format(hint, error),
            c=discord.Color.red(),
        )
        # helpEmbed = (
        #     InterHelp(self.bot)._command_embed(
        #         ctx.interaction, ctx.command, color=discord.Color.red()
        #     )
        #     if ctx.interaction
        #     else InterHelp(self.bot)._command_embed_ctx(
        #         ctx, ctx.command, color=discord.Color.red()
        #     )
        # )
        # await ctx.send(embeds=[hintEmbed, helpEmbed], ephemeral=True)
        await ctx.send(embed=hintEmbed, ephemeral=True)
        ctx.command_failed = True

    async def _interaction_error_handler(inter: discord.Interaction, error: Exception):
        print(error)

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
        }
        hint: str = errorDir.get(
            error, "An unknown erorr has occurred. Please use `/bug` to report this."
        )

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
        try:
            ctx = await commands.Context.from_interaction(
                interaction
            )  # Guarenteed to work with modals (maybe?)
            return await Watchers(ctx.bot).on_command_error(ctx, error)
        except ValueError:
            return await Watchers._interaction_error_handler(interaction, error)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        if "jishaku" in ctx.invoked_parents or "jsk" in ctx.invoked_parents:
            return
        try:
            if ctx.command_failed:
                await ctx.message.add_reaction("\N{DOUBLE EXCLAMATION MARK}")
            else:
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        except HTTPException:
            pass

        except Exception as e:
            raise e

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        pass


async def setup(bot):
    await bot.add_cog(Watchers(bot))
