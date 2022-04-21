
import discord
from discord.ext import commands
from discord import app_commands, Interaction

import requests
import bs4
from typing import Literal


from _aux.embeds import fmte, fmte_i
from Help import EmbedHelp  

class Utility(commands.Cog):
    """
    Helpful stuff
    """
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        pass

    def ge(self):
        return "🔢"
    
    @app_commands.command()
    async def helpmsg(self, inter: Interaction, cog: str = None, group: str = None, command: str = None):
        h = EmbedHelp()
        if cog and not group and not command:
            h.send_cog_help(self.bot.get_cog(cog))
        elif group and not cog and not command:
            h.send_group_help(self.bot.get_group(group))
        elif command and not cog and not group:
            h.send_command_help(self.bot.get_command(command))

    @app_commands.command()
    async def ping(self, inter: Interaction, ephemeral: bool = True):
        """
        Returns the bot's latency, in milliseconds.
        """
        ping = self.bot.latency
        emt = "`🛑 [HIGH]`" if ping>0.4 else "`⚠ [MEDIUM]`"
        emt = emt if ping>0.2 else "`✅ [LOW]`"

        await inter.response.send_message(embed=fmte_i(inter, "🏓 Pong!", f"{round(ping*1000, 3)} miliseconds!\n{emt}"), ephemeral=ephemeral)
    
    @app_commands.command()
    async def bot(self, inter: Interaction):
        """
        Returns information about the bot.
        """
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")
        embed = fmte_i(
            inter,
            t = "Hello! I'm {}.".format(self.bot.user.name),
            d = "Prefix: `<mention> or >>`"
        )
        embed.add_field(
            name = "**__Statistics__**",
            value = "{s}**Creation Date:** <t:{}>{s}**Owners:** {}".format(
                round(self.bot.user.created_at.timestamp()),
                "\n{}".format(bb).join([str(c) for c in (await self.bot.application_info()).team.members]),
                s = b
            )
        )
        await inter.response.send_message(embed=embed, ephemeral=True)
        
    guild = app_commands.Group(name = "guild", description = "...")
    
    @guild.command()
    async def info(self, inter: Interaction, ephemeral: bool = True):
        """
        Returns information on the current server
        """
        guild: discord.Guild = inter.guild
        b = "\n{s}{s}".format(s="ㅤ")
        bb = "\n{s}{s}{s}".format(s="ㅤ")
        embed = fmte_i(
            inter,
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
        await inter.response.send_message(embed=embed, ephemeral=ephemeral)

    @guild.command()
    @commands.has_permissions(manage_channels = True)
    async def channels(self, inter: Interaction, ephemeral: bool = True):
        """
        Returns a list of the server's channels.
        """
        embed = fmte_i(
            inter,
            t = "`{}` has `{}` Channels".format(inter.guild.name, len(inter.guild.channels)),
            d = "\n".join(["**__{}__**:\n{}".format(c.name, "\n".join(["ㅤㅤ{}".format(chan.name) for chan in c.channels])) for c in inter.guild.categories])
        )
        await inter.response.send_message(embed=embed, ephemeral=ephemeral)
    
    @guild.command()
    @commands.has_permissions(manage_messages = True)
    async def dump(self, inter: Interaction, datatype: Literal["channel", "user", "role"], ephemeral: bool = True):
        """
        Returns all of the available bot data on the datatype given.
        """
        data = ""
        if datatype in ["channels", "channel", "chans", "chan"]:
            data = "\n".join(["{}: {}".format(c.name, ", ".join([chan.name for chan in c.channels])) for c in inter.guild.categories])
        open("commanddump.txt", "wb").write(data.encode("utf-8"))
        file = discord.File("commanddump.txt", "commanddump.txt")
        await inter.user.send(file = file)
        embed = fmte_i(
            inter,
            t = "`{}` information on `{}`".format(inter.guild, datatype)
        )
        await inter.response.send_message(embed=embed, file = file, ephemeral=True)
    
    @app_commands.command()
    @commands.is_nsfw()
    async def search(self, inter: Interaction, querey: str, ephemeral: bool = True):
        """
        Searches the web for a website and returns the first result.
        """
        url = "https://www.google.com/search?q={}".format(querey)

        res = requests.get(url)

        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        linkElements = soup.select("div#main > div > div > div > a")

        if len(linkElements) == 0:
            raise commands.errors.BadArgument("Could not find any valid link elements...")
        else:
            link = linkElements[0].get("href")
            i = 0
            while link[0:4] != "/url" or link[14:20] == "google":
                i += 1
                link = linkElements[i].get("href")
        embed = fmte_i(
            inter,
            t = "Result found!",
            d = "*Bot is not responsible for results*"
        )
        await inter.response.send_message(link, embed=embed, ephemeral=ephemeral)


async def setup(bot):
    await bot.add_cog(Utility(bot))