from asyncpg import Connection
import discord
from discord.ext import commands

from pymongo.database import Database
from pymongo.collection import Collection
from typing import Literal, Mapping, List, Optional, Tuple, Union

from src.auxiliary.user.Embeds import fmte
from src.auxiliary.user.Subclass import Paginator
from data.ItemMaps import Chemistry

chem = Chemistry()


class Items(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    def ge(self):
        return "\N{SCHOOL SATCHEL}"

    def getVal(self, item: str):
        """
        Either returns the symbol of the element or raises an error
        """
        if (item := chem.name_to_sym.get(item, None)) is None:  # Check if not full name
            if item := chem.sym_to_name.get(item, None) is None:  # Check if not symbol
                raise ValueError("Invalid element")
        return item

    @commands.hybrid_group()
    async def inv(self, ctx: commands.Context):
        pass

    @inv.command()
    async def show(
        self,
        ctx: commands.Context,
        user: Optional[discord.User],
        sortby: Optional[Literal["amount", "name"]] = "amount",
    ):
        user = user or ctx.author
        items = await ItemDatabase(ctx).getItems(user)

        values = [(item[0], item[1]) for item in items.items()]

        view = InventoryView(ctx, values, sortby)
        embed = view.page_zero(ctx.interaction)
        view.checkButtons()
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @inv.command()
    async def add(
        self,
        ctx: commands.Context,
        item: str,
        amount: int,
        user: Optional[discord.User],
    ):
        user = user or ctx.author
        item: str = self.getVal(item.lower())
        v = await ItemDatabase(ctx).addItem(user, item, amount)
        await ctx.send(v)


class ItemDatabase:
    def __init__(self, ctx: commands.Context):
        self.bot: commands.Bot = ctx.bot
        self.apg: Connection = self.bot.apg

    async def getItems(
        self, user: Union[discord.Member, discord.User]
    ) -> Mapping[str, int]:

        # Need to use * here
        command = """
            SELECT items
            FROM users
            WHERE userid == $1
        """
        result = await self.apg.fetchrow(command, user.id)

        if result is not None:
            return dict(result)

        else:
            command: str = """
                INSERT INTO users
                VALUES ($1, $2, $3)
            """
            # Because the user entry didn't exist, it's okay to give them zero balance
            await self.apg.execute(command, user.id, 0, "{}")
            return {}

    async def addItems(
        self, user: Union[discord.Member, discord.User], itemname: str, amount: int
    ) -> Mapping[str, int]:
        command = """
            UPDATE users
            SET 
        """
        result = await self.apg.fetchrow(command, user.id)

        if result is not None:
            return dict(result)

        else:
            command: str = """
                INSERT INTO users
                VALUES ($1, $2, $3)
            """
            # Because the user entry didn't exist, it's okay to give them zero balance
            await self.apg.execute(command, user.id, 0, "{}")
            return {}


class InventoryView(Paginator):
    def __init__(
        self,
        ctx: commands.Context,
        values: List[Tuple[str, int]],
        sort: Literal["amount", "name"] = "name",
    ):
        # [(sword, 2), (idk, 13)]
        addrs = {
            "name": lambda x: x[0],
            "amount": lambda x: x[1],
        }
        values = sorted(values, key=addrs[sort])
        super().__init__(ctx, values, 5)

    # @overload
    def add_fields(self, embed: discord.Embed):
        start = self.pagesize * (self.position - 1)
        stop = self.pagesize * self.position

        values = self.vals[start:stop]
        for value in values:
            embed.add_field(
                name=f"{value[0].replace('_', ' ').capitalize()}: `{value[1]}`",
                value="ㅤ",
                inline=False,
            )
        return embed

    # @overload
    def embed(self, inter: discord.Interaction):
        embed = fmte(
            self.ctx, t=f"Inventory: Page `{self.position}` / `{self.maxpos or 1}`"
        )
        return embed


async def setup(bot):
    await bot.add_cog(Items(bot))
