import discord
from discord.ext import commands

from typing import Any, List
from math import ceil

from _aux.embeds import fmte, fmte_i, EmbedPaginator, DMEmbedPaginator
from _aux.userio import is_user


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    def ge(self):
        return "👨🏻‍💻"

    # @app_commands.command()
    # @commands.is_owner()
    # async def load(self, ctx, cog: str = "*", logging: bool = True):
    #     """
    #     Loads the bot's cogs
    #     """
    #     log = ""
    #     if cog == "*":
    #         for cog in os.listdir("./cogs"):

    #             if cog.endswith(".py") and not cog.startswith("_"):
    #                 try:
    #                     await self.bot.load_extension(f"cogs.{cog[:-3]}")
    #                     log += f"✅ {cog}\n"

    #                 except commands.errors.ExtensionAlreadyLoaded:
    #                     await self.bot.reload_extension(f"cogs.{cog[:-3]}")
    #                     log += f"✅ {cog}\n"

    #                 except Exception as err:
    #                     print(err)
    #                     log += f"❌ {cog} [{err}]\n"
    #     if logging: await ctx.send(log, ephemeral = True)

    # @app_commands.command()
    # @commands.is_owner()
    # async def get_log(self, inter: Interaction):
    #     """
    #     Returns the bot's commandlog
    #     """
    #     file: discord.File = discord.File("_commandlog.txt", "commandlog.txt")
    #     embed: discord.Embed = fmte_i(
    #         inter,
    #         t = "Log fetched."
    #     )
    # await inter.response.send_message(embed = embed, file = file,
    # ephemeral=True)

    # @app_commands.command()
    # @commands.is_owner()
    # async def kill(self, ctx: commands.Context):
    #     """
    #     Turns off the bot.
    #     """
    #     embed = fmte(
    #         ctx,
    #         t = "Bot Shutting Down..."
    #     )
    #     await ctx.send(embed = embed)
    #     await self.bot.close()

    # @app_commands.command()
    # @commands.is_owner()
    # async def ccache(self, inter: Interaction):
    #     """
    #     Clears the bot's cache
    #     """
    #     self.bot.clear()
    #     embed = fmte_i(
    #         inter,
    #         "Cache cleared."
    #     )
    #     await inter.response.send_message(embed = embed, ephemeral=True)

    # @app_commands.command()
    # @commands.is_owner()
    # async def cmds(self, inter: Interaction):
    #     """
    #     Returns a list of all of the bot's commands
    #     """
    #     data = ""
    #     for c in self.bot.commands:
    #         if hasattr(c, "commands"): # It's a group
    #             data += "\nGroup: {}\nㅤㅤ{}".format(
    #                 c.qualified_name,
    #                 "\nㅤㅤ".join(["{} {}".format(c.name, c.aliases) for c in c.commands])
    #             )
    #         else: # Just a command
    #             data += "\nCommand: {}".format(
    #                 c.qualified_name
    #             )
    # await inter.response.send_message("```{}```".format(data),
    # ephemeral=True)

    @commands.hybrid_command()
    @commands.is_owner()
    async def dms(self, ctx: commands.Context, thing: str):
        """
        Gets all dms from a user
        """
        user = await is_user(ctx, thing)
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
    async def history(self, ctx: commands.Context):
        """
        Create a paginator with buttons for looking through message history
        """
        msgs = []
        async for m in ctx.channel.history(limit=199):
            msgs.append(m)

        embed = fmte(
            ctx,
            t="Waiting for user input...",
        )
        view = EmbedPaginator(
            values=msgs,
            pagesize=10,
            fieldname="content",
            fieldvalue="author",
            defaultname="`No Content`",
            defaultvalue="`No author (?)`"
        )

        msg = await ctx.send(embed=embed, view=view)
        view.response = msg

    # @app_commands.command()
    # @commands.is_owner()
    # async def sigs(self, ctx: commands.Context):
    #     """
    #     Gets signatures of all commands
    #     """
    #     data = ""
    #     for c in self.bot.commands:
    #         if hasattr(c, "commands"): # It's a group
    #             for r in c.commands:
    #                 data += "{}: {}\n".format(r.qualified_name, r.signature)
    #         else:
    #             data += "{} {}\n".format(c.qualified_name, c.signature)
    #     await ctx.send("```{}```".format(data))

    # @app_commands.command()
    # @commands.is_owner()
    # async def dm(self, ctx: commands.Context, user: str):
    #     """
    #     Dms a user
    #     """
    #     embed = fmte(
    #         ctx,
    #         t = "Please send the message to be sent to the user."
    #     )
    #     await ctx.send(embed = embed)
    #     ms: discord.Message = await self.bot.wait_for("message", check = lambda m: m.author == ctx.author)
    #     user: discord.User = await is_user(ctx, user)
    #     if not user:
    #         embed = fmte(
    #             ctx,
    #             t = "Cannot find that user."
    #         )
    #         await ctx.send(embed = embed)
    #         return
    #     urls = "\n".join([c.url for c in ms.attachments])
    #     await user.send(
    #         content = "{}\n{}".format(ms.content, urls),
    #         embeds = ms.embeds,
    #     )


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
