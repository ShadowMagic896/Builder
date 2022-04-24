from asyncore import close_all
from pydoc import describe
import discord
from discord import app_commands, Interaction
from discord.ext import commands

import os
from typing import Any, List, Optional, Union


from _aux.embeds import fmte, fmte_i

class InterHelp(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_command()
    async def help(self, ctx: commands.Context, item: str = None):
        """
        Get a guide on what I can do.
        """
        if not item:
            embed = fmte(
                ctx,
                t = "Help",
                d = "Hello there! {}\n**Cogs:** `{}`\n**Commands:** `{}`".format(
                    (await self.bot.application_info()).description,
                    len(self.bot.cogs),
                    len(self.bot.commands)
                )
            )
            
            
            view = HelpMenu().add_item(CogSelect(self.bot))
            
            await ctx.send(embed=embed, view=view, ephemeral=True)
        cogs = [v for c, v in self.bot.cogs.items() if c.lower() == item.lower()]
        if len(cogs) != 0:
            embed = InterHelp(self.bot)._cog_embed(ctx.interaction, cogs[0])
            view = HelpMenu().add_item(CogSelect(self.bot)).add_item(CommandSelect(self.bot, cogs[0]))
            await ctx.send(embed=embed, view=view)
            return
        commands = [c for c in self.get_cmds() if c.name.lower() == item.lower()]
        if len(commands) != 0:
            embed = InterHelp(self.bot)._command_embed(ctx.interaction, commands[0])
            view = HelpMenu().add_item(CogSelect(self.bot)).add_item(CommandSelect(self.bot, commands[0].cog))
            await ctx.send(embed=embed, view=view)
            return
        else:
            embed = fmte(
                ctx,
                t = "Hm... I Couldn't Find That",
                d = "Please choose an option from below."
            )
            view = HelpMenu().add_item(CogSelect(self.bot))
            await ctx.send(embed=embed, view=view)
            

        

    @help.autocomplete("item")
    async def item_autocomplete(self, inter: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        ac: List[Union[commands.Cog, commands.HybridCommand]] = [c for c in self.bot.commands]
        
        for c, v in self.bot.cogs.items():
            if c in os.getenv("FORBIDDEN_COGS").split(";"):
                continue
            ac.append(v)
            
        return [
            discord.app_commands.Choice(name=f"{c.qualified_name} [{'COG' if isinstance(c, commands.Cog) else 'COMMAND'}]", value=c.qualified_name)
            for c in ac
            if current.lower() in c.qualified_name.lower() or c.qualified_name.lower() in current.lower()
        ][:25]

        
    
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
        
        view = HelpMenu().add_item(self).add_item(CommandSelect(self.bot, obj))

        await interaction.response.edit_message(embed=embed, view=view)

class CommandSelect(discord.ui.Select): # Shows all commands from a certain cog
    def __init__(self, bot: commands.Bot, cog: commands.Cog):
        placeholder = "Command Selection..."
        options = []
        self.bot = bot
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
        command: commands.HybridCommand = self.bot.get_command(interaction.data["values"][0])
        embed = fmte_i(
            interaction,
            t = "`{}` [Cog: `{}`, Group: `{}`]".format(
                command.qualified_name,
                command.cog_name,
                command.parent
            ),
            d = "```{} {}```\n*{}*".format(
                command.qualified_name, command.signature,
                command.short_doc
            )
        )
        view = HelpMenu().add_item(CogSelect(self.bot)).add_item(self)
        await interaction.response.edit_message(embed=embed, view=view)

class CloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close", emoji="❌", style=discord.ButtonStyle.red)
        self.message: discord.Message = None
    
    async def callback(self, interaction: Interaction) -> Any:
        await self.message.delete()

async def setup(bot):
    await bot.add_cog(InterHelp(bot))