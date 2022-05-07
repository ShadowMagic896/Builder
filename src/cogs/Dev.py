from subprocess import Popen
import discord
from discord import app_commands
from discord.app_commands import describe
from discord.ext import commands

from typing import Any, List, Literal, Mapping
from math import ceil

from _aux.embeds import fmte, fmte_i, EmbedPaginator, DMEmbedPaginator
from _aux.Converters import TimeConvert
from cogs.MixedHelp import MixedHelp


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    def ge(self):
        return "👨🏻‍💻"

    @commands.hybrid_command()
    @commands.is_owner()
    async def dms(self, ctx: commands.Context, user: discord.Member):
        """
        Gets all dms from a user
        """
        channel = await self.bot.create_dm(user)
        msgs = []
        async for m in channel.history(limit=300):
            msgs.append(m)
        print(len(msgs))
        embed = fmte(
            ctx,
            t="Waiting for user input...",
        )
        view = DMEmbedPaginator(
            values=msgs,
            pagesize=10,
            fieldname="content",
            fieldvalue="attachments",
            defaultname="`No Content`",
            defaultvalue="`No Attachments`"
        )

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    @commands.is_owner()
    async def history(self, ctx: commands.Context, user: discord.Member):
        """
        Create a paginator with buttons for looking through the user's message history
        """
        msgs = []
        async for m in user.history(limit=200):
            msgs.append(m)
        embed = fmte(
            ctx,
            t="Waiting for user input...",
        )
        view = EmbedPaginator(
            values=msgs,
            pagesize=10,
            fieldname="content",
            fieldvalue="created_at",
            defaultname="`No Content`",
            defaultvalue="`No Timestamp`"
        )

        msg = await ctx.send(embed=embed, view=view)
        view.response = msg

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
                     len(MixedHelp(self.bot).explode(l)))
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def timetest(self, ctx: commands.Context, time: TimeConvert):
        await ctx.send(str(time))


async def setup(bot):
    await bot.add_cog(Dev(bot))


class DM_Menu(discord.ui.View):
    def __init__(self, mlist):
        super().__init__()
        self.pagesize = 10
        self.pos = 0
        self.posmax = ceil((len(mlist) - 1) / self.pagesize)
        self.mlist: List[discord.Message] = mlist

    @discord.ui.button(label="<")
    async def back(self, inter: discord.Interaction, _: Any):
        self.pos -= 1
        if self.pos < 0:
            self.pos = self.posmax
        embed = fmte_i(
            inter,
            t="[{}/{}]".format(self.pos + 1, self.posmax + 1),
        )
        for mes in self.mlist[self.pagesize *
                              (self.pos - 1):self.pagesize * self.pos]:
            embed.add_field(
                name=mes.content if mes.content else "`NO CONTENT`",
                value=", ".join([a.url for a in mes.attachments]
                                ) if mes.attachments else "`NO ATTACHMENTS`",
                inline=False
            )
        await inter.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌")
    async def close(self, inter: discord.Interaction, _: Any):
        await inter.delete_original_message()

    @discord.ui.button(label=">")
    async def next(self, inter: discord.Interaction, _: Any):
        self.pos += 1
        if self.pos > self.posmax:
            self.pos = 0
        embed = fmte_i(
            inter,
            t="[{}/{}]".format(self.pos + 1, self.posmax + 1),
        )
        for mes in self.mlist[self.pagesize *
                              (self.pos - 1):self.pagesize * self.pos]:
            embed.add_field(
                name=mes.content if mes.content else "`NO CONTENT`",
                value=", ".join([a.url for a in mes.attachments]
                                ) if mes.attachments else "`NO ATTACHMENTS`",
                inline=False
            )
        await inter.response.edit_message(embed=embed, view=self)
