import discord
from discord import Interaction, app_commands
from discord.app_commands import describe
from discord.ext import commands

import translate
import googletrans
import langdetect
import langcodes
import pycountry

from typing import Optional

from src._aux.embeds import Desc, fmte, fmte_i


class Language(commands.Cog):
    """
    Commands for anything that has to do with language.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._translateMenu: app_commands.ContextMenu = app_commands.ContextMenu(
            name = "Translate Message",
            callback = self.translateMenu,
        )
        self.bot.tree.add_command(self._translateMenu)
    
    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self._translateMenu.type)
        return await super().cog_unload()

    def ge(self):
        return "🌎"

    @commands.hybrid_command()
    @describe(message="The message to translate.",
              dest="The target translation language. Can be lang code or full name. Defaults to English.",
              ephemeral=Desc.ephemeral)
    async def translate(self, ctx: commands.Context, message: str, dest: Optional[str] = "en", ephemeral: bool = False):
        """
        Translates a message using google's Google Translate API.
        """
        trans = googletrans.Translator().translate(text=message, dest=dest, src="auto")

        embed = fmte(
            ctx,
            t=trans.text,
            d="**From:** `{}`\n**To:** `{}`\n".format(googletrans.LANGUAGES[trans.src].capitalize(
            ), googletrans.LANGUAGES[trans.dest].capitalize())
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    # @app_commands.context_menu(name="Translate Message")
    async def translateMenu(self, inter: Interaction, message: discord.Message) -> None:
        trans = googletrans.Translator().translate(
            text=message.content, dest="en", src="auto")
        embed = fmte_i(
            inter,
            t=trans.text,
            d="**From:** `{}`\n**To:** `{}`\n".format(googletrans.LANGUAGES[trans.src].capitalize(
            ), googletrans.LANGUAGES[trans.dest].capitalize())
        )
        await inter.response.send_message(embed=embed)

    @commands.hybrid_command()
    @describe(
        message="The message to get the language of.",
        ephemeral=Desc.ephemeral,
    )
    async def language(self, ctx: commands.Context, message: str, ephemeral: bool = False):
        """
        Gets the estimated language of any message
        """
        lang = googletrans.Translator().detect(message)
        embed = fmte(
            ctx,
            t="`%s`" % googletrans.LANGUAGES[lang.lang]
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

    @commands.hybrid_command()
    async def speakers(self, ctx: commands.Context, language: str, ephemeral: bool = False):
        """
        Gets the estimated
        """
        lang = langcodes.get(self.getLangCode(language))
        pop = lang.speaking_population()
        embed = fmte(
            ctx,
            t=pop,
            d="{}".format(lang.__str__(), lang.display_name())
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)


async def setup(bot):
    await bot.add_cog(Language(bot))
