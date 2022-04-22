from typing import Optional
import discord
from discord import app_commands, Interaction
from discord.ext import commands

import os

from _aux.embeds import fmte, fmte_i

class InterHelp(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @app_commands.command()
    async def helpmsg(self, inter: Interaction, cog: str = None, group: str = None, command: str = None, ephemeral: bool = True):
        if cog and not group and not command:
            self.raisecog(cog)
            embed = self.get_cog_help(cog)
            await inter.response.send_message(embed=embed, ephemeral=ephemeral)
        elif group and not cog and not command:
            self.raisegroup(group)
            embed = self.get_group_help(cog)
            await inter.response.send_message(embed=embed, ephemeral=ephemeral)
        elif command and not cog and not group:
            self.raisecommand(command)
            embed = self.get_command_help(command)
            await inter.response.send_message(embed=embed, ephemeral=ephemeral)

    def get_cmds(self):
        coms = [
            c for c in self.bot.commands
            if not isinstance(c, app_commands.Group)
        ]
        for g in [g for g in self.bot.commands if isinstance(g, app_commands.Group)]:
            coms.extend(g.commands)
        return coms

    def raisecog(self, cog: str):
        e = commands.errors.ObjectNotFound(cog) if cog not in [c.name for c, v in self.bot.cogs.items()] else None
        if e: raise e
    
    def raisegroup(self, group: str):
        e = commands.errors.ObjectNotFound(group) if group not in [g.name for g in self.bot.commands if isinstance(g, app_commands.Group)] else None
        if e: raise e
    
    def raisecommand(self, command: str):
        e = commands.errors.ObjectNotFound(command) if command not in self.get_cmds() else None
        if e: raise e
    
    def cog_view(self):
        return Menu().add_item(
            CogSelect(
                placeholder="Cog Select", 
                options=[c.name for c, v in self.bot.cogs.items() if c.name not in os.getenv("FORBIDDEN_COGS").split(";")]
            )
        )



class Menu(discord.ui.View):
    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
    
class CogSelect(discord.SelectOption):
    def __init__(self, ctx: commands.Context, *, placeholder, options) -> None:
        super().__init__(placeholder=placeholder, options=options)
        self.ctx = ctx

    async def callback(self, inter: discord.Interaction):
        if self.ctx.author != inter.user: return
        opt: str = inter.data["values"][0]
        obj: commands.Cog = self.ctx.bot.get_cog(opt)

        embed = fmte_i(
            inter,
            t = "`{}` [Cog]".format(opt),
            d = "Commands: `{}`".format(len(obj.get_commands()))
        )
        
        view = Menu().add_item(self).add_item(
            CommandSelect(self.ctx, placeholder="Command Select", options=obj.get_commands())
        )

        inter.edit_original_message(embed=embed, view=view)
        
class CommandSelect(discord.SelectOption):
    def __init__(self, ctx: commands.Context, *, placeholder, options, cog: commands.Cog) -> None:
        super().__init__(placeholder=placeholder, options=options)
        self.ctx = ctx
        self.cog = cog
    
    def callback(self, inter: discord.Interaction):
        if self.ctx.author != inter.user: return
        opt: str = inter.data["values"][0]
        obj: app_commands.Command = self.ctx.bot.get_command(opt)

        embed = fmte_i(
            inter,
            t = "`{}` [Command]\nCog: `{}` Group: `{}`".format(obj.name, self.cog, obj.parent),
            d = "*{}*\n`/{} {}`".format(obj.description, obj.name)
        )

