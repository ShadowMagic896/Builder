from math import floor
from pydoc import describe
import discord
from discord.ext import commands


from _aux.embeds import fmte

class Utility(commands.Cog):
    """
    This cog is for any commands that help users find information about other users, this bot, the server, etc.
    """

    def __init__(self, bot: commands.Bot) -> None:
        pass
    
    @commands.hybrid_group()
    async def builder(self, ctx):
        await self.help(ctx)

    @builder.command()
    async def ping(self, ctx: commands.Context):
        """
        Returns the bot's latency, in milliseconds.
        Usage: >>ping
        """
        ping=ctx.bot.latency
        emt="`🛑 [HIGH]`" if ping>0.4 else "`⚠ [MEDIUM]`"
        emt=emt if ping>0.2 else "`✅ [LOW]`"

        await ctx.send(embed=fmte(ctx, "🏓 Pong!", f"{round(ping*1000, 3)} miliseconds!\n{emt}"))
    
    @builder.command()
    async def help(self, ctx):
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")
        embed = fmte(
            ctx,
            t = "Hello! I'm {}.".format(ctx.bot.user.name),
            d = "Prefix: `>>`"
        )
        embed.add_field(
            name = "**__Statistics__**",
            value = "{s}**Creation Date:** <t:{}>{s}**Owners:** {}".format(
                round(ctx.bot.user.created_at.timestamp()),
                "\n{}".format(bb).join([str(c) for c in (await ctx.bot.application_info()).team.members]),
                s = b
            )
        )
        await ctx.send(embed=embed)
    @commands.hybrid_group()
    async def guild(self, ctx: commands.Context):
        pass
    
    @guild.command()
    async def info(self, ctx: commands.Context):
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
        await ctx.send(embed=embed)

    
    @guild.command(aliases = ["chan", "chans", "channel"])
    async def channels(self, ctx: commands.Context):
        embed = fmte(
            ctx,
            t = "`{}` has `{}` Channels".format(ctx.guild.name, len(ctx.guild.channels)),
            d = "\n".join(["**__{}__**:\n{}".format(c.name, "\n".join(["ㅤㅤ{}".format(chan.name) for chan in c.channels])) for c in ctx.guild.categories])
        )
        await ctx.send(embed=embed)
    
    @guild.command(aliases = ["allinfo", "get"])
    # @commands.has_permissions(manage_messages = True)
    async def dump(self, ctx: commands.Context, datatype: str):
        data = ""
        if datatype in ["channels", "channel", "chans", "chan"]:
            data = "\n".join(["{}: {}".format(c.name, ", ".join([chan.name for chan in c.channels])) for c in ctx.guild.categories])
        open("commanddump.txt", "wb").write(data.encode("utf-8"))
        file = discord.File("commanddump.txt", "commanddump.txt")
        await ctx.author.send(file = file)
        embed = fmte(
            ctx,
            t = "Guild information on {} sent to {}.".format(datatype, ctx.author)
        )
        await ctx.send(embed = embed)
        


async def setup(bot):
    await bot.add_cog(Utility(bot))