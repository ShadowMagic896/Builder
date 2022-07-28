from typing import Literal

import discord
import pytenno
from discord.app_commands import describe
from discord.ext import commands
from pytenno.models.enums import Platform

from ..utils.abc import BaseCog, Paginator
from ..utils.bot_types import Builder, BuilderContext


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
    @describe(
        item_name="The name of the item to get",
        order_type="The type of the order",
        platform="The platform of the orders",
        sort_type="What to sort the results by",
        sort_method="How to sort the results. 'ascending' is lowest to highest, 'descending' is highest to lowest",
    )
    async def get_orders(
        self,
        ctx: BuilderContext,
        item_name: str,
        order_type: Literal["buy", "sell", "any"] = "buy",
        platform: Literal["pc", "ps4", "switch", "xbox"] = "pc",
        sort_type: Literal["platinum", "creation_date", "last_update"] = "platinum",
        sort_method: Literal["ascending", "descending"] = "ascending",
    ):
        """Get all orders for a specific item"""
        orders = await self.bot.tenno.items.get_orders(
            item_name=item_name,
            include_items=False,
            platform=Platform[platform],
        )
        view = ItemOrdersView(
            ctx,
            sorted(
                filter(
                    lambda o: (o.order_type.name == order_type)
                    if (order_type != "any")
                    else (True),
                    orders,
                ),
                key=lambda o: getattr(o, sort_type),
                reverse=sort_method == "descending",
            ),
            order_type,
            item_name,
        )
        await view.update()
        embed = await view.page_zero(ctx.interaction)
        view.message = await ctx.send(embed=embed, view=view)

    @get_orders.autocomplete("item_name")
    async def get_orders_item_name_autocomplete(
        self, ctx: BuilderContext, current: str
    ):

        # I could do listcomp here, but then I'll iterate over the entire list of items, even if I already have 25 selections
        # For other autocompletes this effect is negligable, but bot.caches.WFM_items is about 2875 items
        items = []
        for cached in self.bot.caches.WFM_items:
            if len(items) >= 25:
                break
            if (cu := current.lower()) in (ca := cached.lower()) or ca in cu:
                items.append(
                    discord.app_commands.Choice(
                        name=cached,
                        value=cached,
                    )
                )

        return items

    @items.command()
    @describe(language="The language of the item data")
    async def all(
        self,
        ctx: BuilderContext,
        language: Literal[
            "en", "ru", "ko", "fr", "sv", "de", "zh_hans", "zh_hant", "pt", "es", "pl"
        ] = "en",
    ):
        """Fetch limited data on all (tradeable) items"""
        items = await self.bot.tenno.items.get_items(language=language)
        items.sort(key=lambda i: i.url_name)
        view = AllItemDataView(ctx, items)
        await view.update()
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


class AllItemDataView(Paginator):
    def __init__(
        self,
        ctx: BuilderContext,
        items: list[pytenno.models.items.ItemShort],
    ):
        self.items = items
        super().__init__(ctx, items, pagesize=5)

    async def adjust(self, embed: discord.Embed):
        items: list[pytenno.models.items.ItemShort] = self.value_range
        for c, item in enumerate(items):
            embed.add_field(
                name=f"`{self.format_absoloute(c)}`: **`{item.item_name}`** [`{item.url_name}`]",
                value=f"**WFM ID:** `{item.id}`\n"
                f"**Icon:** [View Image]({item.thumb})\n",
                inline=False,
            )
        return embed

    async def embed(self, inter: discord.Interaction):
        return await self.ctx.format(
            title=f"All Item Data [Page `{self.position+1}` of `{self.maxpos+1}`]"
        )


async def setup(bot: Builder):
    await bot.add_cog(WFM(bot))
