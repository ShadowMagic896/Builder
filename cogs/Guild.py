import discord
from discord.app_commands import describe
from discord.ext import commands

from typing import Literal

from _aux.embeds import fmte_i, fmte
from _aux.sql3OOP import Table
from _aux.userio import clean


class Guild(commands.Cog):
    """
    Commands for managing or getting information about this guild.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def ge(self):
        return "🏠"
    
    @commands.hybrid_command()
    @describe(
        ephemeral = "Whether to publicly show the response to the command.",
    )
    async def guildinfo(self, ctx: commands.Context, ephemeral: bool = False):
        """
        Returns information on the current server
        """
        guild: discord.Guild = ctx.guild
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")
        embed = fmte(
            ctx,
            t = "Info: {} [{}]".format(guild.name, guild.id),
            d = guild.description
        )
        embed.add_field(
            name = "***__General Info__***",
            value = "{s}**Owner**: {} [{}]{s}**Created:**: <t:{}>{s}**Nitro Level:** {}".format(
                guild.owner, guild.owner_id,
                round(guild.created_at.timestamp()),
                guild.premium_tier,
                s = b
            ),
            inline = False
        )
        embed.add_field(
            name = "***__User Info__***",
            value = "{s}**Users:** {}{s}**Bots:** {}{s}**Boosters:** {}{s}**Total:** {}".format(
                len([p for p in guild.members if not p.bot]),
                len([p for p in guild.members if p.bot]),
                guild.premium_subscription_count,
                len(guild.members),
                s = b
            ),
            inline = False
        )
        embed.add_field(
            name = "***__Customization__***",
            value = "{s}**Vanity URL:** {}{s}**Emojis: **{} / {}{s}**Stickers:** {} / {}".format(
                guild.vanity_url,
                len(guild.emojis), guild.emoji_limit,
                len(guild.stickers), guild.sticker_limit,
                s = b
            ),
            inline = False
        )
        embed.add_field(
            name = "***__Statistics__***",
            value = "{s}**Veri. Level:** {}{s}**Max Filesize:** {}{s}**VC Bitrate:** {} bytes{s}**NSFW Level:** {}{s}**Locale:** {}{s}**Other featues:** {}".format(
                guild.verification_level.name.capitalize(),
                guild.filesize_limit,
                guild.bitrate_limit,
                guild.nsfw_level.name.capitalize(),
                guild.preferred_locale,
                "\n{}".format(bb).join(guild.features) if len(guild.features) > 0 else "{}None\n".format(bb),
                s = b
            )
        )
        if guild.banner:
            embed.set_image(url = guild.banner.url)
        await ctx.send(embed=embed, ephemeral=ephemeral)
    
    @commands.hybrid_command()
    @commands.has_permissions(manage_messages = True)
    @describe(
        datatype = "The type of data to return.",
        ephemeral = "Whether to publicly show the response to the command.",
    )
    async def dump(self, ctx: commands.Context, datatype: Literal["channel", "user", "role"], ephemeral: bool = False):
        """
        Returns all of the available bot data on the datatype given.
        """
        data = ""
        if datatype in ["channels", "channel", "chans", "chan"]:
            data = "\n".join(["{}: {}".format(c.name, ", ".join([chan.name for chan in c.channels])) for c in ctx.guild.categories])
        open("commanddump.txt", "wb").write(data.encode("utf-8"))
        file = discord.File("commanddump.txt", "commanddump.txt")
        await ctx.user.send(file = file)
        embed = fmte_i(
            ctx,
            t = "`{}` information on `{}`".format(ctx.guild, datatype)
        )
        await ctx.send(embed=embed, file = file, ephemeral=ephemeral)


async def setup(bot: commands.Bot):
    await bot.add_cog(Guild(bot))