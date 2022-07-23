from typing import Literal

import discord
import pytenno
from discord.app_commands import describe
from discord.ext import commands
from pytenno.models.enums import Platform

from ..utils.bot_types import Builder, BuilderContext
from ..utils.subclass import BaseCog, Paginator


class WFM(BaseCog):
    """Cog for interacting with warframe.market"""

    def ge(self):
        return "\N{CROSSED SWORDS}"

    @commands.hybrid_group()
    async def wfm(self, ctx: BuilderContext):
        pass

    @wfm.group()
    async def items(self, ctx: BuilderContext):
        pass

    @items.command()
    async def get_orders(
        self,
        ctx: BuilderContext,
        item_name: str,
        order_type: Literal["buy", "sell"] = "buy",
        platform: Literal["pc", "ps4", "switch", "xbox"] = "pc",
    ):
        """Get the current orders for an item"""
        orders = await self.bot.tenno.items.get_orders(
            item_name=item_name,
            include_items=False,
            platform=Platform[platform],
        )
        view = ItemOrdersView(
            ctx,
            [o for o in orders if o.order_type.name == order_type],
            order_type,
            item_name,
        )
        embed = await view.page_zero(ctx.interaction)
        view.message = await ctx.send(embed=embed, view=view)
        self.bot.tenno.items.get_item()

    @items.command()
    async def get_data(
        self,
        ctx: BuilderContext,
        item_name: str,
        platform: Literal["pc", "ps4", "switch", "xbox"] = "pc",
        language: Literal[
            "en", "ru", "ko", "fr", "sv", "de", "zh_hans", "zh_hant", "pt", "es", "pl"
        ] = "en",
    ):
        items = await self.bot.tenno.items.get_item(
            item_name=item_name, platform=Platform[platform]
        )
        view = ItemDataView(ctx, items, item_name, language)
        embed = await view.page_zero(ctx.interaction)
        view.message = await ctx.send(embed=embed, view=view)


class ItemOrdersView(Paginator):
    def __init__(
        self,
        ctx: BuilderContext,
        orders: list[pytenno.models.orders.OrderRow],
        order_type: str,
        item_name: str,
    ):
        self.orders = orders
        self.order_type = order_type
        self.item_name = item_name
        super().__init__(ctx, orders, pagesize=5)

    async def adjust(self, embed: discord.Embed):
        for order in self.value_range:
            order: pytenno.models.orders.OrderRow
            embed.add_field(
                name=f"`{order.user.ingame_name}`: `{order.platinum}`<:_:1000247886862372965>",
                value=f"ㅤ**Created At:** <t:{int(order.creation_date.timestamp())}:R>\n"
                f"ㅤ**Last Updated:** <t:{int(order.last_update.timestamp())}:R>\n"
                f"ㅤ**Order Quantity:** `{order.quantity}`\n",
                inline=False,
            )
        return embed

    async def embed(self, inter: discord.Interaction):
        return await self.ctx.format(
            title=f"{self.order_type.capitalize()} Orders for {self.item_name} [Page `{self.position+1}` of `{self.maxpos+1}`]"
        )


class ItemDataView(Paginator):
    def __init__(
        self,
        ctx: BuilderContext,
        items: list[pytenno.models.items.ItemFull],
        item_name: str,
        language: str,
    ):
        self.items = items
        self.item_name = item_name
        self.language = language
        super().__init__(ctx, items, pagesize=1)

    async def adjust(self, embed: discord.Embed):
        item: pytenno.models.items.ItemFull = self.value_range[0]
        tr: pytenno.models.items.LangInItem = getattr(item, self.language)
        embed.description = f"**`{item.url_name}`**"
        embed.add_field(name="**Name**", value=f"`{tr.item_name}`", inline=False)
        embed.add_field(
            name="**Description**", value=f"`{tr.description}`", inline=False
        )
        embed.add_field(
            name="**Required Mastery Rank**",
            value=f"`{item.mastery_level}`",
            inline=False,
        )
        embed.add_field(
            name="**Is Set Root**", value=f"`{item.set_root}`", inline=False
        )
        embed.add_field(
            name="**# Needed for Set**",
            value=f"`{item.quantity_for_set}`",
            inline=False,
        )
        embed.url = tr.wiki_link
        embed.set_image(url=item.sub_icon)
        return embed

    async def embed(self, inter: discord.Interaction):
        return await self.ctx.format(
            title=f"Item Data: `{self.item_name}` [Page `{self.position+1}` of `{self.maxpos+1}`]"
        )


async def setup(bot: Builder):
    await bot.add_cog(WFM(bot))
