from discord.ext import commands

import pyfiglet
from pyfiglet import Figlet

from _aux.embeds import fmte

class Fun(commands.Cog):
    """Commands that are designed to be fun to use!"""

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.hybrid_command()
    async def font(self, ctx, font: str, *, text: str):
        """
        Turns your text into a new font!
        Usage: >>font <font> <*text>
        """
        try:
            t = Figlet(font).renderText(" ".join(text))
            embed = fmte(ctx, t = "Rendering Finished!")
            if len(t) > 1990:
                embed.set_footer(text = "Requested by {}\n[Tuncated because of size]".format(ctx.author))
            await ctx.message.reply("```{}```".format(t[:1990]), embed = embed)
                
        except pyfiglet.FontNotFound:
            embed = fmte(
                ctx,
                t = "Sorry, I can't find that font.",
                d = "Maybe try another one, or use `>>help font` for all fonts",
            )
            await ctx.message.reply(embed = embed)

    
    



    
            
async def setup(bot):
    await bot.add_cog(Fun(bot))