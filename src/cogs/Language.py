from re import I
from typing import List, Optional, Tuple, Union
from typing_extensions import Self
import discord
from discord.app_commands import describe
from discord.ext import commands
from numpy import fix

from translate import Translator
import langdetect
import langcodes
from iso639 import languages
import pycountry
import translate

from _aux.embeds import Desc, fmte

class Language(commands.Cog):
    """
    Commands for anything that has to do with language.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def ge(self):
        return "🌎"
        
    def allLangCodes(self):
        return [country.alpha_2 for country in pycountry.countries]
    
    def getLangCode(self, msg: str):
        try: # Full name
            lang = langcodes.find_name("language", msg).language
            fixdict = {
                "enc": "en"
            }
            if lang in fixdict.keys():
                return fixdict[lang]
            return lang
        except LookupError:
            if x := langcodes.get(msg): # Just a code
                return (x.language)
        raise commands.errors.BadArgument(msg)
        
    def getLangName(self, code: str):
        return langcodes.get(code)

    
    @commands.hybrid_command()
    @describe(
        message = "The message to translate.",
        fromlang = "The source of the language. Can be lang code or full name. If none is given, one will be inferred.",
        tolang = "The target translation language. Can be lang code or full name. Defaults to English.",
        ephemeral = Desc.ephemeral
    )
    async def translate(self, ctx: commands.Context, message: str, fromlang: Optional[str] = None, tolang: Optional[str] = "en-US", ephemeral: bool = False):
        """
        Translates a message. Specify source language for a more accurate translation.
        """

        if fromlang is None:
            fromlang = langdetect.detect(message) 
        else:
            fromlang = self.getLangCode(fromlang)
            
        tolang = self.getLangCode(tolang)
        message = translate.Translator(to_lang=tolang, from_lang=fromlang).translate(message)
        fromlang, tolang = langcodes.get(fromlang).display_name(), langcodes.get(tolang).display_name()

        embed = fmte(
            ctx,
            t = message,
            d = "**From:** {}\n**To:** {}\n".format(fromlang, tolang, )
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)
    
    @commands.hybrid_command()
    @describe(
        message = "The message to get the language of.",
        outputlang = "The language of the output ('French' vs. 'Français').",
        ephemeral = Desc.ephemeral,
    )
    async def language(self, ctx: commands.Context, message: str, outputlang: str = "en", ephemeral: bool = False):
        """
        Gets the estimated language of any message
        """
        lang = self.getLangName(langdetect.detect(message))
        embed = fmte(
            ctx,
            t = lang.display_name()
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
            t = pop,
            d = "{} [{}]".format(lang.__str__(), lang.display_name())
        )
        await ctx.send(embed=embed, ephemeral=ephemeral)

async def setup(bot):
    await bot.add_cog(Language(bot))