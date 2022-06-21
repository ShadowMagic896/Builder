from typing import Callable, Optional
import discord
from discord.app_commands import describe
from discord.ext import commands
from unidecode import unidecode_expect_nonascii
import json as js

from src.utils.bot_types import Builder, BuilderContext
from src.utils.embeds import fmte
from src.utils.constants import Const
from src.utils import errors
from src.utils.subclass import BaseCog, BaseView


class Misc(BaseCog):
    """
    Commands that don't fit into any one category
    """

    def ge(self):
        return "\N{BLACK QUESTION MARK ORNAMENT}"

    @commands.hybrid_command()
    @describe(message="The message to decancer")
    async def decancer(self, ctx: BuilderContext, message: str):
        """
        Converts a message into plain latin characters
        """
        decoded = unidecode_expect_nonascii(message, errors="ignore")
        embed = fmte(ctx, t="Message Decancered")
        embed.add_field(name="Before", value=message, inline=False)
        embed.add_field(name="After", value=decoded, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def affirmation(self, ctx: BuilderContext):
        """
        You are a good person
        """
        url: str = Const.URLs.AFFIRMATION_API
        response = await self.bot.session.get(url, ssl=False)
        json: dict = await response.json()
        quote: str = json["affirmation"]

        embed = fmte(ctx, t=quote)
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    @describe(
        id="The specific advice ID to get"
    )
    async def advice(self, ctx: BuilderContext, id: Optional[int] = None):
        """
        Gives you life advice
        """
        if id is not None:
            url: str = Const.URLs.ADVICE_API + f"/{id}"
        else:
            url: str = Const.URLs.ADVICE_API
        response = await self.bot.session.get(url, ssl=False)

        json: dict = js.loads(await response.text())
        if json.get("slip", None) is None:
            raise commands.errors.BadArgument("Couldn't find advice")

        id_, advice = json["slip"]["id"], json["slip"]["advice"]

        embed = fmte(ctx, t=advice, d=f"ID: `{id_}`")
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def dog(self, ctx: BuilderContext):
        """
        Gets a random picture of a doggo
        """
        url = Const.URLs.DOG_API
        response = await self.bot.session.get(url)
        json = await response.json()
        if json["status"] != "success":
            raise errors.InternalError("Cannot reach API")
        view = NewImgView(ctx, url, lambda x: x["message"])
        embed = fmte(ctx)
        embed.set_image(url=json["message"])

        view.message = await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    async def cat(self, ctx: BuilderContext):
        """
        Gets a random picture of a catto
        """
        url: str = f"{Const.URLs.CAT_API}/cat?json=true"
        response = await self.bot.session.get(url, ssl=False)
        json = await response.json()

        view = NewImgView(ctx, url, lambda x: f"{Const.URLs.CAT_API}/{x['url']}")
        embed = fmte(ctx)
        embed.set_image(url=f"{Const.URLs.CAT_API}/{json['url']}")

        view.message = await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    async def fox(self, ctx: BuilderContext):
        """
        Get a random picute of a foxxo
        """
        url: str = Const.URLs.FOX_API
        response = await self.bot.session.get(url, ssl=False)
        json = await response.json()
        view = NewImgView(ctx, url, lambda x: x["image"])
        embed = fmte(ctx)
        embed.set_image(url=json["image"])

        view.message = await ctx.send(embed=embed, view=view)

    @commands.hybrid_command()
    async def duck(self, ctx: BuilderContext):
        """
        Get a random picture of a ducky
        """
        url: str = Const.URLs.DUCK_API
        response = await self.bot.session.get(url, ssl=False)
        json = await response.json()
        view = NewImgView(ctx, url, lambda x: x["url"])
        embed = fmte(ctx)
        embed.set_image(url=json["url"])

        view.message = await ctx.send(embed=embed, view=view)


class NewImgView(BaseView):
    def __init__(
        self,
        ctx: BuilderContext,
        url: str,
        accessor: Callable[[dict], str],
        timeout: Optional[float] = 300,
    ):
        self.url = url
        self.accessor = accessor
        super().__init__(ctx, timeout)

    @discord.ui.button(
        label="New Image",
        emoji="\N{Clockwise Rightwards and Leftwards Open Circle Arrows}",
    )
    async def ag(self, inter: discord.Interaction, button: discord.ui.Button):
        embed: discord.Embed = inter.message.embeds[0]

        response = await self.ctx.bot.session.get(self.url, ssl=False)
        json = await response.json()

        embed.set_image(url=self.accessor(json))
        await inter.response.edit_message(embed=embed)

    @discord.ui.button(emoji="\N{CROSS MARK}", style=discord.ButtonStyle.danger)
    async def close(self, inter: discord.Interaction, button: discord.ui.Button):
        for v in self.children:
            v.disabled = True
        await inter.response.edit_message(view=self)


async def setup(bot: Builder):
    await bot.add_cog(Misc(bot))
