from discord.ext import commands

import os

from src.ext.Embeds import fmte


class GitHub(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group()
    @commands.is_owner()
    async def git(self, ctx: commands.Context):
        pass

    @git.command()
    async def push(self, ctx: commands.Context, message: str):
        command = "git add -A && git commit -am '%s' && git push origin main" % message
        os.system(command)
        embed = fmte(ctx, t="Code Successfully Pushed", d="```\n%s\n```" % command)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(GitHub(bot))
