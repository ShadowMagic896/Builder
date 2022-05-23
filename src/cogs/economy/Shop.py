from typing import Iterable, List, Optional, Union
import asyncpg
import discord
from discord.app_commands import Range, describe
from discord.ext import commands
from pyrsistent import v
from data.errors import MissingShopEntry
from src.auxiliary.user.Subclass import BaseView, Paginator
from src.auxiliary.bot.Constants import CONSTANTS
from data.ItemMaps import Chemistry, getAtomicName

from src.auxiliary.user.Converters import Atom
from src.auxiliary.user.Embeds import fmte
from src.cogs.economy.Atoms import AtomsDatabase


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_group()
    async def shop(self, ctx: commands.Context):
        pass

    @shop.command()
    @describe(
        atom="The atom to sell. Can be atom name, symbol, or atomic number",
        amount="How many to sell",
        price="The price at which to sell ALL of the atoms at",
    )
    async def post(
        self,
        ctx: commands.Context,
        atom: Atom,
        amount: Range[int, 1, len(Chemistry().names)],
        price: Range[int, 1],
    ):
        """
        Creates a new posting selling atoms for coins.
        """
        await AtomsDatabase(ctx).registerUser(ctx.author)

        useratoms = await AtomsDatabase(ctx).getAtoms(ctx.author)
        urec = [rec for rec in useratoms if rec["atomid"] == atom]
        atomname = Chemistry().names[atom - 1]

        if len(urec) == 0 or urec[0]["count"] < amount:
            raise ValueError(f"You don't have that much `{atomname}`!")

        rec = await ShopDatabase(ctx).createShop(ctx.author, atom, amount, price)
        identity = rec["identity"]
        await AtomsDatabase(ctx).giveAtom(ctx.author, atom, -amount)

        embed = fmte(
            ctx,
            t="Shop Listing Created!",
            d=f"**Atom:** `{atomname}` [ID: `{atom}`]\n**Amount:** `{amount}`\n**Price:** `{price}`{CONSTANTS.Emojis().COIN_ID}\n**Listing ID:** `{identity}`",
        )
        await ctx.send(embed=embed)

    @shop.command()
    @describe(
        listingid="The ID of the listing to remove. Can be gotten by using viewing all of your shops"
    )
    async def unpost(self, ctx: commands.Context, listingid: Range[int, 1]):
        """
        Removes a posting from the market and refunds your atoms.
        """
        res = await ShopDatabase(ctx).getShop(listingid)
        if res is None:
            raise ValueError("Cannot find a shop listing with that ID.")
        if res["userid"] != ctx.author.id:
            raise commands.errors.MissingPermissions("This is not your posting.")
        await ShopDatabase(ctx).removeShop(res["identity"])
        atomname = getAtomicName(res["atomid"])
        atom = res["atomid"]
        amount = res["amount"]
        price = res["price"]
        embed = fmte(
            ctx,
            t="Listing Successfully Removed",
            d=f"***__Listing Information__***\n**Atom:** `{atomname}` [ID: `{atom}`]\n**Amount:** `{amount}`\n**Price:** `{price}`{CONSTANTS.Emojis().COIN_ID}\n**Listing ID:** `{listingid}`",
        )
        await ctx.send(embed=embed)

        await AtomsDatabase(ctx).giveAtom(ctx.author, atom, amount)

    @shop.command()
    @describe(
        atom="Only view shops selling this atom", user="Only view shops by this user"
    )
    async def view(
        self, ctx: commands.Context, atom: Optional[Atom], user: Optional[discord.User]
    ):
        """
        Shows all shop entries meeting certain criteria.
        """
        db = ShopDatabase(ctx)
        if user is None:
            # Fetch vals from all users
            if atom is None:
                vals = await db.getAll()
            else:
                vals = await db.getWithAttrs("atomid = $1", atom)
            vals = sorted(vals, key=lambda r: r["price"] / r["amount"])
            view = ShopView(ctx, vals, 10)
        else:
            if atom is None:
                vals = await db.getBy(user)
            else:
                vals = await db.getWithAttrs(
                    "atomid = $1 AND userid = $2", atom, user.id
                )
            vals = sorted(vals, key=lambda r: r["price"] / r["amount"])
            view = PersonalShopView(ctx, user, vals, 10)
        embed = view.page_zero(ctx.interaction)
        view.checkButtons()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @shop.command()
    async def info(self, ctx: commands.Context, transactionid: Range[int, 1]):
        shop: asyncpg.Record = await ShopDatabase(ctx).getShop(transactionid)
        if shop is None:
            raise ValueError(
                "A shop with this ID does not exist. Maybe it was deleted, or you misspelled something."
            )
        author = self.bot.get_user(shop["userid"])
        atomid = shop["atomid"]
        atomname = getAtomicName(atomid)
        amount = shop["amount"]
        price = shop["price"]
        embed = fmte(
            ctx,
            t=f"Information for Shop ID: `{transactionid}`",
            d=f"**Author:** `{author}`\n**Atom:** `{atomname}`\n**Atom ID:** `{atomid}`\n**Amount:** `{amount}`\n**Price:** `{price}`",
        )
        await ctx.send(embed=embed, view=PurchaseView(ctx, shop))


class ShopDatabase:
    def __init__(self, ctx: commands.Context) -> None:
        self.ctx: commands.Context = ctx
        self.apg: asyncpg.Connection = ctx.bot.apg

    async def getAll(self):
        command = """
            SELECT * FROM shops
        """
        return await self.apg.fetch(command)

    async def getAllBy(
        self, users: Optional[List[Union[discord.User, discord.Member]]]
    ) -> List[asyncpg.Record]:
        ids = str(tuple([user.id for user in users]))
        fmtd = ids[:-2] + ids[-1:]
        command = f"""
            SELECT * FROM shops
            WHERE userid IN {fmtd}
        """
        allEntries: List[asyncpg.Record] = await self.apg.fetch(command)
        return allEntries

    async def getBy(self, user: discord.User):
        command = """
            SELECT * FROM shops
            WHERE userid = $1
        """
        return await self.apg.fetch(command, user.id)

    async def delete(self, identity: int) -> str:
        command = """
            DELETE FROM shops
            WHERE identity = $1
            RETURNING *
        """
        return await self.apg.fetchrow(command, identity)

    async def createShop(
        self,
        user: Union[discord.Member, discord.User],
        atomid: int,
        amount: int,
        price: int,
    ) -> asyncpg.Record:
        """
        Creates a shop entry. Returns the transaction's record.
        """
        command = """
            INSERT INTO shops(userid, atomid, amount, price)
            VALUES (
                $1,
                $2,
                $3,
                $4
            )
            ON CONFLICT(userid, atomid) DO UPDATE
            SET amount = $3, price = $4
            RETURNING *
        """
        return await self.apg.fetchrow(command, user.id, atomid, amount, price)

    async def getShop(self, identity: int):
        command = """
            SELECT * FROM shops
            WHERE identity = $1
        """
        return await self.apg.fetchrow(command, identity)

    async def removeShop(self, identity: int) -> List[asyncpg.Record]:
        command = """
            DELETE FROM shops
            WHERE identity = $1
            RETURNING *
        """
        return await self.apg.fetchrow(command, identity)

    async def getWithAttrs(self, wherestr: str, *args):
        command = f"""
            SELECT * FROM shops
            WHERE {wherestr}
        """
        return await self.apg.fetch(command, *args)


class ShopView(Paginator):
    def __init__(
        self,
        ctx: commands.Context,
        values: Iterable,
        pagesize: int,
        *,
        timeout: Optional[float] = 45,
    ):
        super().__init__(ctx, values, pagesize, timeout=timeout)

    def adjust(self, embed: discord.Embed):
        start = self.pagesize * (self.position - 1)
        stop = self.pagesize * self.position

        for shop in self.vals[start:stop]:
            name = getAtomicName(shop["atomid"])
            amt = shop["amount"]
            price = shop["price"]
            coin = CONSTANTS.Emojis().COIN_ID

            transid = shop["identity"]

            embed.add_field(
                name=f"`{name} [{amt}]` -> `{price}`{coin}",
                value=f"**Transaction ID:** `{transid}`",
                inline=False,
            )
        return embed

    def embed(self, inter: discord.Interaction):
        embed = fmte(
            self.ctx, t=f"Shops: Page `{self.position}` / `{self.maxpos or 1}`"
        )
        return embed


class PersonalShopView(Paginator):
    def __init__(
        self,
        ctx: commands.Context,
        user: Union[discord.User, discord.Member],
        values: Iterable,
        pagesize: int,
        *,
        timeout: Optional[float] = 45,
    ):
        self.user = user
        super().__init__(ctx, values, pagesize, timeout=timeout)

    def adjust(self, embed: discord.Embed):
        start = self.pagesize * (self.position - 1)
        stop = self.pagesize * self.position

        for shop in self.vals[start:stop]:
            name = getAtomicName(shop["atomid"])
            amt = shop["amount"]
            price = shop["price"]
            transid = shop["identity"]
            coin = CONSTANTS.Emojis().COIN_ID

            embed.add_field(
                name=f"`{name} [{amt}]` -> `{price}`{coin}",
                value=f"**Transaction ID:** `{transid}`",
            )
        return embed

    def embed(self, inter: discord.Interaction):
        embed = fmte(
            self.ctx,
            t=f"`{self.user}`'s Shops: Page `{self.position}` / `{self.maxpos or 1}`",
        )
        return embed


class PurchaseView(BaseView):
    def __init__(
        self,
        ctx: commands.Context,
        record: asyncpg.Record,
        timeout: Optional[float] = 45,
    ):
        self.record = record
        super().__init__(ctx, timeout)

    @discord.ui.button(
        label="Purchase", emoji="\N{MONEY BAG}", style=discord.ButtonStyle.primary
    )
    async def purchase(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user.id == self.record["userid"]:
            raise commands.errors.MissingPermissions(
                "You cannot purchase your own shop!"
            )
        pass

    @discord.ui.button(
        label="Remove", emoji="\N{CROSS MARK}", style=discord.ButtonStyle.danger
    )
    async def destroy(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user.id != self.record["userid"]:
            raise commands.errors.MissingPermissions(
                "You cannot delete a shop that isn't yours!"
            )
        result = await ShopDatabase(self.ctx).delete(self.record["identity"])
        if result is None:
            raise MissingShopEntry("Cannot find shop, it was most likely deleted.")
        else:
            atomname = getAtomicName(result["atomid"])
            atom = result["atomid"]
            amount = result["amount"]
            price = result["price"]
            listingid = result["identity"]
            embed = fmte(
                self.ctx,
                t="Listing Successfully Removed",
                d=f"***__Listing Information__***\n**Atom:** `{atomname}` [ID: `{atom}`]\n**Amount:** `{amount}`\n**Price:** `{price}`{CONSTANTS.Emojis().COIN_ID}\n**Listing ID:** `{listingid}`",
            )
            await inter.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Shop(bot))
