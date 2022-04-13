from client_container import *

class Fun(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
    
    @commands.command()
    async def font(self, ctx, font: str, text: str):
        try:
            t = Figlet(font).renderText(" ".join(text))
            embed = fmte(ctx, t = "Rendering Finished!")
            await ctx.send("```{}```".format(t), embed = embed)
                
        except pyfiglet.FontNotFound:
            embed = fmte(
                ctx,
                t = "Sorry, I can't find that font.",
                d = "Maybe try another one, or use `>>help font` for all fonts",
            )
            await ctx.send(embed = embed)

            
async def setup(bot):
    await bot.add_cog(Fun(bot))