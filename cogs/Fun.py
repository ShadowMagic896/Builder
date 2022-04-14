from client_container import *

class Fun(commands.Cog):
    """Commands that are designed to be fun to use!"""

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.hybrid_command(name="font")
    async def font(self, ctx, font: Literal[
            "3-d", "ascii___", "banner3-D", "charset_", "gothic", "hollywood", "linux", "lockergnome", "lexible_", 
            "platoon_", "mike", "mini", "mirror", "mnemonic",  "modern__", "morse", "moscow", "slant", "trek", 
            "wavy", "weird", "tomahawk", "usaflag", 
        ], *, text: str):
        """
        Turns your text into a new font!
        Usage: >>font <font> <*text>
        """
        try:
            t = Figlet(font).renderText(" ".join(text))
            embed = fmte(ctx, t = "Rendering Finished!")
            if len(t) > 1990:
                embed.set_footer(text = "Requested by {}\n[Tuncated because of size]".format(ctx.author))
            await ctx.send("```{}```".format(t[:1990]), embed = embed)
                
        except pyfiglet.FontNotFound:
            embed = fmte(
                ctx,
                t = "Sorry, I can't find that font.",
                d = "Maybe try another one, or use `>>help font` for all fonts",
            )
            await ctx.send(embed = embed)

            
async def setup(bot):
    await bot.add_cog(Fun(bot))