import discord
from discord.ext import commands

from pymongo.database import Database
from pymongo.collection import Collection
from typing import Literal, Mapping, List, Optional, Tuple

from src.auxiliary.user.Embeds import fmte
from src.auxiliary.user.Subclass import Paginator
from data.ItemMaps import Chemistry

chem = Chemistry()


class Items(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    def ge(self):
        return "\N{SCHOOL SATCHEL}"

    @commands.hybrid_group()
    async def inv(self, ctx: commands.Context):
        pass

    @inv.command()
    async def show(self, ctx: commands.Context, user: Optional[discord.User]):
        user = user or ctx.author
        items = await ItemDatabase(ctx).getItems(user)

        values = [(item[0], item[1]) for item in items.items()]

        view = InventoryView(ctx, values, "name")
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
        item = item.lower()
        # Helium
        # Helium: He
        # He: Helium
        if (item := chem.name_to_sym.get(item, None)) is None:  # Check if not full name
            if item := chem.sym_to_name.get(item, None) is None:  # Check if not symbol
                raise ValueError("Invalid element")
        print(item)
        v = await ItemDatabase(ctx).addItem(user, item, amount)
        await ctx.send(v)


class ItemDatabase:
    def __init__(self, ctx: commands.Context):
        self.bot: commands.Bot = ctx.bot
        self.database: Database = self.bot.database
        self.collections: Mapping[str, Collection] = self.bot.collections

    async def checkForExist(self, user: discord.User) -> bool:
        """
        Checks for a user's existence in the database. If it is not there, it creates a new entry with the ID of the user.
        Returns whether a new entry was created.
        """
        if self.collections["items"].find_one({"userid": user.id}) is None:
            self.collections["items"].insert_one({"userid": user.id, "items": {}})
            return True
        return False

    async def addItem(
        self, user: discord.User, itemid: str, amount: int, autoremove: bool = True
    ) -> Mapping[str, int]:
        """
        Adds an item to the user's inventory
        Returns the user's new items
        """
        result = self.collections["items"].find_one_and_update(
            {"userid": user.id},
            {"$inc": {f"items.{itemid}": amount}},
            upsert=True,
            return_document=True,
        )
        if result["items"][itemid] < 1 and autoremove:
            result = await self.removeItem(user, itemid)

        return result["items"] if not autoremove else result

    async def removeItem(self, user: discord.User, itemid: str):
        """
        Removes all of a user's items of a certain ID.
        Returns the user's new items
        """
        self.collections["items"].update_one(
            {"userid": user.id}, {"$unset": {f"items.{itemid}": ""}}
        )
        return await self.getItems(user)

    async def setItems(self, user: discord.User, items: Mapping[str, int]) -> None:
        """
        Sets a user's items.
        """
        self.collections["items"].replace_one(
            filter={"userid": user.id},
            replacement={"$set": {"items": items}},
            upsert=True,
        )

    async def getItems(self, user: discord.User) -> Mapping[str, int]:
        """
        Get a list of all items for some user
        """
        result = self.collections["items"].find_one({"userid": user.id})
        if result is None:
            self.collections["items"].insert_one(
                document={"userid": user.id, "items": {}}
            )
        return result["items"] if result is not None else {}

    async def delete(self, user: discord.User) -> None:
        """
        Deletes a user's entry
        """
        self.collections["balances"].delete_one({"userid": user.id})


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
