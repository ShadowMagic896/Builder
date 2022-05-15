import os
from subprocess import Popen
import time
import discord
from discord import app_commands
from discord.app_commands import describe
from discord.ext import commands

from typing import Any, List, Literal, Mapping
from math import ceil

from src.auxiliary.user.Embeds import fmte, fmte_i
from src.auxiliary.user.UserIO import explode
from src.auxiliary.user.Converters import TimeConvert


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
    
    @commands.hybrid_command()
    @commands.is_owner()
    @describe(
        params="The arguments to pass to Popen & autopep8"
    )
    async def fmtcode(self, ctx, params: str = "-aaair"):
        """
        Formats the bot's code using autopep8
        """
        Popen(
            "py -m autopep8 %s R:\\VSCode-Projects\\Discord-Bots\\Builder" %
            params,).stdout
        await ctx.send("Code formatting completed.")

    @commands.hybrid_command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: str = None):
        if spec:
            l: List[app_commands.AppCommand] = await self.bot.tree.sync(guild=ctx.guild)
        else:
            l: List[app_commands.AppCommand] = await self.bot.tree.sync()
        embed = fmte(ctx, t="%s Commands Synced" %
                     len(explode(l)))
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def timetest(self, ctx: commands.Context, time: TimeConvert):
        await ctx.send(str(time))
    
    @commands.hybrid_command()
    async def docker(self, ctx: commands.Context):
        await ctx.interaction.response.send_modal(CodeModal(ctx))

class CodeModal(discord.ui.Modal):
    def __init__(self, ctx) -> None:
        self.ctx: commands.Context = ctx
        super().__init__(title="Code Evaluation")
    code = discord.ui.TextInput(
        label="Please paste / type code here",
        style=discord.TextStyle.long
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        estart = time.time()
        value = self.code.value.replace("^", "**")

        basepath = "data\containers"

        # Create a new directory that will contain the Dockerfile and python file
        _dir = len(os.listdir(basepath))
        _dir = 0
        dirpath = f"{basepath}\{_dir}"
        os.system(f"cd {os.getcwd()}\{dirpath}")

        # The user's code
        pypath = f"{dirpath}\main.py"
        # The Dockerfile
        dockerpath = f"{dirpath}\Dockerfile"
        # Dockerfile template
        templatepath = "data\DockerfileTemplate.txt"

        with open(pypath, "w") as pyfile:
            pyfile.write(value)

        with open(dockerpath, "w") as dockerfile:
            with open(templatepath, "r") as template:
                dockerfile.write(template.read())


        pylog = f"{os.getcwd()}\\{dirpath}\\pythonlog.log"
        os.system(f"cd {dirpath} && docker build -t {_dir} . && docker run --stop-timeout 3 {_dir} > {pylog}")
        with open(pylog, "r") as log:
            # To manage the line and character output
            fmtlog = "".join(log.readlines()[:20])[:3900]
            embed = fmte(
                self.ctx,
                d = f"**Code:**\n```py\n{value}\n```\n**Result:**```\n{fmtlog}\nFinished in: {time.time() - estart} seconds```"
            )
            await interaction.followup.send(content=None, embed=embed)
        os.system("docker system prune -fa")
        os.remove(dirpath)



async def setup(bot):
    await bot.add_cog(Dev(bot))