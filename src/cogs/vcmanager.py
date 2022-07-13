import discord
from discord.ext import commands
from settings import DEVELOPMENT_GUILD_IDS
from typing import Dict, List, NamedTuple

from ..utils.bot_types import BuilderContext

from ..utils.subclass import BaseCog


STARTER: int = 0

class Emojis:
    closed_lock = "\N{LOCK}"
    open_lock = "\N{OPEN LOCK}"
    closed_lock_with_key = "\N{CLOSED LOCK WITH KEY}"
    lock_with_ink_pen = "\N{LOCK WITH INK PEN}"

class ActiveChannel(NamedTuple):
    channel: discord.TextChannel
    owner_id: int

active_channels: List[ActiveChannel] = []

class VCManager(BaseCog):
    @commands.Cog.listener()
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if after.channel is not None and after.channel.id == STARTER: # Moved to starter channel
            overwrites = discord.PermissionOverwrite()
            overwrites.speak = True
            overwrites.priority_speaker = True
            channel: discord.VoiceChannel = await after.channel.category.create_voice_channel(
                name=member.name,
                overwrites={member: overwrites}
            )
            await member.move_to(channel)
            active_channels.append(ActiveChannel(channel, member.id))
        elif active := [c for c in active_channels if c.channel == before.channel]:
            if len(active[0].channel.members) == 0:
                await active[0].channel.delete()
                active_channels.remove(active[0])

    @commands.hybrid_command()
    @commands.is_owner()
    @discord.app_commands.guilds(*DEVELOPMENT_GUILD_IDS)
    async def _init_controller(self, ctx: BuilderContext):
        embed = format(
            color=0x2F3136, # Embed background, rounded colors
            title="Manage **Voice Channel**",
            description=
                f"{Emojis.closed_lock} - **Lock** Channel\n"
                f"{Emojis.open_lock} - **Unlock** Channel\n"
                f"{Emojis.closed_lock_with_key} - **Hide** Channel\n"
                f"{Emojis.lock_with_ink_pen} - **Reveal** Channel\n"
        )
        
        # I would appreciate if you didn't remove this, but I can't really do anything about it lol
        view = ControllerView()
        await ctx.send(embed=embed, view=view)

class ControllerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        emoji=Emojis.closed_lock,
        custom_id="vc_button_lock"
    )
    async def lock_channel(self, inter: discord.Interaction, button: discord.ui.Button):
        if await self._set_perms(
            inter,
            default_perms={"connect": False, "speak": False, "stream": False},
        ):
            await inter.response.send_message("You channel has been **LOCKED**", ephemeral=True)

    @discord.ui.button(
        emoji=Emojis.open_lock,
        custom_id="vc_button_unlock"
    )
    async def unlock(self, inter: discord.Interaction, button: discord.ui.Button):
        if await self._set_perms(
            inter,
            default_perms={"connect": True, "speak": True, "stream": True},
        ):
            await inter.response.send_message("You channel has been **UNLOCKED**", ephemeral=True)

    @discord.ui.button(
        emoji=Emojis.closed_lock_with_key,
        custom_id="vc_button_hide"
    )
    async def hide(self, inter: discord.Interaction, button: discord.ui.Button):
        if await self._set_perms(
            inter,
            default_perms={"view_channel": False},
        ):
            await inter.response.send_message("You channel has been **HIDDEN**", ephemeral=True)


    @discord.ui.button(
        emoji=Emojis.lock_with_ink_pen,
        custom_id="vc_button_reveal"
    )
    async def reveal(self, inter: discord.Interaction, button: discord.ui.Button):
        if await self._set_perms(
            inter,
            default_perms={"view_channel": True},
        ):
            await inter.response.send_message("You channel has been **REVEALED**", ephemeral=True)

    async def _set_perms(self, inter: discord.Interaction, default_perms: Dict[str, bool]):
        start_channel = inter.guild.get_channel(STARTER)
        # Assuming I have the correct ID here, this will never be None

        active = discord.utils.get(
            active_channels,
            owner_id=inter.user.id,
        )
        if active is None:
            await inter.response.send_message(
                f"You do not have any channel!\nJoin {start_channel.mention} to enter." ,
                ephemeral=True
            )
            return False
        perms = dict(active.channel.permissions_for(inter.guild.default_role))
        perms.update(default_perms)
        overwrite = discord.PermissionOverwrite(**perms)
        await active.channel.set_permissions(inter.guild.default_role, overwrite=overwrite)

        return True 


async def setup(bot: commands.Bot):
    await bot.add_cog(VCManager(bot))
