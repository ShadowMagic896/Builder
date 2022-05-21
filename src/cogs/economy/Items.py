from asyncpg import Connection, Record
import asyncpg
import discord
from discord.app_commands import Range
from discord.ext import commands

from typing import Literal, List, Optional, Tuple, Union

from src.auxiliary.user.Embeds import fmte, fmte_i
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
            if (
                item := chem.sym_to_name.get(item, None)
            ) is None:  # Check if not symbol
                raise ValueError("Invalid element")
        return item

    async def tryRegister(self, ctx: commands.Context, user: discord.User):
        await ItemDatabase(ctx).registerUser(user)

    @commands.hybrid_group()
    async def items(self, ctx: commands.Context):
        pass

    @items.command()
    async def raw(self, ctx: commands.Context, user: Optional[discord.User] = None):
        user = user or ctx.author
        await self.tryRegister(ctx, user)
        result = await ItemDatabase(ctx).getItems(user)
        await ctx.send(result if result is not None else "***No Record.***")

    @items.command()
    async def give(
        self,
        ctx: commands.Context,
        itemid: int,
        amount: Range[int, 0, 1000],
        user: Optional[discord.User] = None,
    ):
        user = user or ctx.author
        await self.tryRegister(ctx, user)
        await ItemDatabase(ctx).giveItem(user, itemid, amount)
        await ctx.send(f"Added {amount} items of {itemid} to {user}.")

    @items.command()
    async def create(self, ctx: commands.Context, itemname: str, description: str):
        await ItemDatabase(ctx).createItem(itemname, description)
        itemid = (await ItemDatabase(ctx).getItem(itemname=itemname))["itemid"]
        await ctx.send(
            f"Item Created\nName: {itemname}\nDescription: {description}\nID: {itemid}"
        )

    @items.command()
    async def all(self, ctx: commands.Context):
        """
        Shows a list of all items you can get.
        """
        values: List[Record] = await ItemDatabase(ctx).allItems()

        view = ItemsView(ctx, values=values, title="All Items", sort="itemid")
        embed = view.page_zero(ctx.interaction)
        view.checkButtons()

        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @items.command()
    @discord.app_commands.choices(
        sort=[
            discord.app_commands.Choice(name=x, value=y)
            for x, y in [
                ("By ID", "itemid"),
                ("By name", "name"),
                ("By amount", "count"),
            ]
        ]
    )
    async def view(
        self,
        ctx: commands.Context,
        user: Optional[discord.User],
        sort: Optional[str] = "itemid",
    ):
        """
        Shows all items that a user has.
        """
        user = user or ctx.author
        values: Union[List[Record], List] = await ItemDatabase(ctx).getItems(user)
        view = ItemsView(ctx, values=values, title=f"`{ctx.author}`'s Items", sort=sort)
        embed = view.page_zero(ctx.interaction)
        view.checkButtons()

        message = await ctx.send(embed=embed, view=view)
        view.message = message


class ItemDatabase:
    def __init__(self, ctx: commands.Context):
        self.bot: commands.Bot = ctx.bot
        self.apg: Connection = self.bot.apg

    async def getItems(
        self, user: Union[discord.Member, discord.User]
    ) -> asyncpg.Record:
        command = """
            SELECT *
            FROM inventories
                INNER JOIN items
                    USING(itemid)
            WHERE userid = $1
        """
        return await self.apg.fetch(command, user.id)

    async def giveItem(
        self, user: Union[discord.Member, discord.User], itemid: int, amount: int
    ) -> asyncpg.Record:
        command = """
            INSERT INTO inventories
            VALUES (
                $1::BIGINT,
                $2::INTEGER,
                $3::INTEGER
            )
            ON CONFLICT(itemid) DO UPDATE
            SET count = inventories.count + $3
        """
        return await self.apg.execute(command, user.id, itemid, amount)

    async def createItem(
        self, name: str, description: Optional[str] = "No Description"
    ) -> str:
        """
        Adds an item to the database. Returns the status of the command.
        """
        command = """
            INSERT INTO items(name, description)
            VALUES (
                $1::TEXT,
                $2::TEXT
            )
        """
        return await self.apg.execute(command, name, description)

    async def deleteItem(self, itemid: int) -> str:
        """
        Deletes an item from the database. Returns the status of the command.
        """
        command = """
            DELETE FROM items
            WHERE itemid = $1
        """
        return await self.apg.execute(command, itemid)

    async def getItem(
        self,
        *,
        itemname: Optional[str] = None,
    ) -> Optional[asyncpg.Record]:
        """
        Returns an `asyncpg.Record` of an item, by either its name or id.
        """
        command = f"""
            SELECT *
            FROM items
            WHERE name = $1
        """
        result = await self.apg.fetchrow(command, itemname)
        return result

    async def registerUser(self, user: discord.User):
        command = """
            INSERT INTO users(userid)
            VALUES (
                $1
            )
            ON CONFLICT DO NOTHING
        """
        await self.apg.execute(command, user.id)

    async def allItems(self):
        return await self.apg.fetch("SELECT * FROM items")


class ItemsView(Paginator):
    def __init__(
        self,
        ctx: commands.Context,
        *,
        values: List[Record],
        title: str,
        sort: str = "id",
    ):
        values = sorted(values, key=lambda x: x[sort])
        self.title = title
        super().__init__(ctx, values, 5)

    def adjust(self, embed: discord.Embed):
        start = self.pagesize * (self.position - 1)
        stop = self.pagesize * self.position

        values = self.vals[start:stop]
        for value in values:
            embed.add_field(
                name=f"{value['name']}: `{value['count']}`",
                value=value["description"],
                inline=False,
            )
        return embed

    def embed(self, inter: discord.Interaction):
        embed = fmte(
            self.ctx, t=f"{self.title}: Page `{self.position}` / `{self.maxpos or 1}`"
        )
        return embed


async def setup(bot):
    await bot.add_cog(Items(bot))
