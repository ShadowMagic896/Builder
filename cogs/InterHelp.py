from ipaddress import v4_int_to_packed
from typing import List, Literal, Mapping, Optional
import discord
from discord import app_commands, Interaction
from discord.ext import commands

import os
from typing import Mapping, Any

from setuptools import Command


from _aux.embeds import fmte, fmte_i

class InterHelp(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_command()
    async def help(self, ctx: commands.Context, ephemeral: bool = True):
        embed = fmte(
            ctx,
            t = "Help Screen",
            d = "Hello! I'm {}.\n{}\nCogs: `{}`\nCommands: `{}`".format(
                self.bot.user.display_name,
                (await self.bot.application_info()).description,
                len(self.bot.cogs),
                len(self.bot.commands)
            )
        )
        view = HelpMenu().add_item(CogSelect(self.bot))
        await ctx.send(embed=embed, view=view, ephemeral=ephemeral)
    
    def get_cmds(self):
        coms = [
            c for c in self.bot.commands
            if not isinstance(c, app_commands.Group)
        ]
        for g in [g for g in self.bot.commands if isinstance(g, app_commands.Group)]:
            coms.extend(g.commands)
        return coms

    def raisecog(self, cog: str):
        for c, v in self.bot.cogs.items():
            if c.lower() == cog.lower():
                return v
        else:
            raise commands.errors.ExtensionNotFound(cog)
    
    def raisegroup(self, group: str):
        for n, g in [(g.name, g) for g in self.bot.commands if isinstance(g, app_commands.Group)]:
            if group.lower() == n.lower():
                return g
        else:
            raise commands.errors.ExtensionNotFound(group)
    
    def raisecommand(self, command: str):
        e = commands.errors.ExtensionNotFound(command) if command not in self.get_cmds() else None
        if e: raise e

        for c in self.get_cmds():
            if c.name.lower() == command:
                return c
        else:
            raise commands.errors.ExtensionNotFound(command)
    


    def cog_embed(self, ctx, cog: commands.Cog):
        return fmte(
            ctx,
            t = "Cog: `{}`".format(cog.qualified_name),
            d = "**Commands:** {}\n*{}*".format(len(cog.get_commands()), cog.description)
        )
    
    def group_embed(self, ctx, group: commands.HybridGroup):
        return fmte(
            ctx,
            t = "Group: `{}`".format(group.qualified_name),
            d = "**Commands:** {}\n*{}*".format(len(group.commands), group.description)
        )
    
    def command_embed(self, ctx, command: commands.HybridCommand):
        return fmte(
            ctx,
            t = "Command: `{}`".format(command.name),
            d = "`/{} {}`\n*{}*".format(command.qualified_name, command.signature, command.short_doc)
        )

    def _cog_embed(self, inter, cog: commands.Cog):
        return fmte_i(
            inter,
            t = "Cog: `{}`".format(cog.qualified_name),
            d = "**Commands:** {}\n*{}*".format(len(cog.get_commands()), cog.description)
        )
    
    def _group_embed(self, inter, group: commands.HybridGroup):
        return fmte_i(
            inter,
            t = "Group: `{}`".format(group.qualified_name),
            d = "**Commands:** {}\n*{}*".format(len(group.commands), group.description)
        )
    
    def _command_embed(self, inter, command: commands.HybridCommand):
        return fmte_i(
            inter,
            t = "Command: `{}`".format(command.name),
            d = "`/{} {}`\n*{}*".format(command.qualified_name, command.signature, command.short_doc)
        )
    


class HelpMenu(discord.ui.View): # Base to add things on
    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)

class CogSelect(discord.ui.Select): # Shows all cogs in the bot
    def __init__(self, bot: commands.Bot):
        placeholder = "Cog Selection..."
        options = []
        self.bot = bot
        for name, cog in bot.cogs.items():
            if name in os.getenv("FORBIDDEN_COGS").split(";"):
                continue
            options.append(
                discord.SelectOption(
                    label = name,
                    description = cog.description,
                    emoji = cog.ge()
                )
            )
        super().__init__(
            placeholder=placeholder,
            options=options,
        )
    
    async def callback(self, interaction: Interaction) -> Any:
        opt = interaction.data["values"][0]
        obj = self.bot.get_cog(opt)

        embed = InterHelp(self.bot)._cog_embed(interaction, obj)
        view = HelpMenu().add_item(self).add_item(CommandSelect(obj))

        await interaction.response.edit_message(embed=embed, view=view)

class CommandSelect(discord.ui.Select): # Shows all commands from a certain cog
    def __init__(self, cog: commands.Cog):
        placeholder = "Command Selection..."
        options = []
        for command in cog.get_commands():
            options.append(
                discord.SelectOption(
                    label = command.qualified_name,
                    description = command.short_doc
                )
            )
        super().__init__(
            placeholder=placeholder,
            options=options, 
        )
    
    async def callback(self, interaction: Interaction) -> Any:
        pass # tbi



async def setup(bot):
    await bot.add_cog(InterHelp(bot))