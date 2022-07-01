from typing import Any, Iterable, List, Optional, Union
import asyncpg
import discord
from discord.app_commands import Range, describe
from discord.ext import commands
from src.utils.errors import MissingShopEntry, MissingFunds, SelfAction, Unowned
from src.utils.item_maps import Chemistry, get_atomic_name

from src.utils.converters import Atom
from src.utils.embeds import format
from src.cogs.atoms import AtomsDatabase
from src.cogs.currency import BalanceDatabase
from src.utils.subclass import BaseCog, BaseView, Paginator
from src.utils.constants import Emojis
from src.utils.bot_types import BuilderContext


class Shop(BaseCog):
    """
    Manipulate the stock market
    """

    def ge(self):
        return "\N{Convenience Store}"

    @commands.hybrid_group()
    async def shop(self, ctx: BuilderContext):
        pass

    @shop.command()
    @describe(
        atom="The atom to sell. Can be atom name, symbol, or atomic number",
        amount="How many to sell",
        price="The price at which to sell ALL of the atoms at",
    )
    async def post(
        self,
        ctx: BuilderContext,
        atom: Atom,
        amount: Range[int, 1],
        price: Range[int, 1],
    ):
        """
        Creates a new posting selling atoms for coins.
        """
        await AtomsDatabase(ctx).register_user(ctx.author)

        useratoms = await AtomsDatabase(ctx).get_atoms(ctx.author)
        urec = [rec for rec in useratoms if rec["atomid"] == atom]
        atomname = Chemistry().names[atom - 1]

        if len(urec) == 0 or urec[0]["count"] < amount:
            raise MissingFunds(f"You don't have that much `{atomname}`!")

        rec = await ShopDatabase(ctx).create(ctx.author, atom, amount, price)
        identity = rec["identity"]
        await AtomsDatabase(ctx).give_atom(ctx.author, atom, -amount)

        embed = await format(
            ctx,
            title="Shop Listing Created!",
            desc=f"**Atom:** `{atomname}` [ID: `{atom}`]\n**Amount:** `{amount:,}`\n**Price:** `{price:,}`{Emojis.COIN_ID}\n**Listing ID:** `{identity}`",
        )
        await ctx.send(embed=embed)

    @shop.command()
    @describe(
        listing="The ID of the listing to remove. Can be gotten by using viewing all of your shops"
    )
    async def remove(self, ctx: BuilderContext, listing: Range[int, 1]):
        """
        Removes a posting from the market and refunds your atoms.
        """

        res = await ShopDatabase(ctx).get_shop(listing)
        if res is None:
            raise MissingShopEntry("Cannot find a shop listing with that ID.")
        if res["userid"] != ctx.author.id:
            raise Unowned("This is not your posting.")
        await ShopDatabase(ctx).remove(res["identity"])
        atomname = get_atomic_name(res["atomid"])
        atom = res["atomid"]
        amount = res["amount"]
        price = res["price"]
        embed = await format(
            ctx,
            title="Listing Successfully Removed",
            desc=f"***__Listing Information__***\n**Atom:** `{atomname}` [ID: `{atom}`]\n**Amount:** `{amount:,}`\n**Price:** `{price:,}`{Emojis.COIN_ID}\n**Listing ID:** `{listing}`",
        )
        await ctx.send(embed=embed)

        await AtomsDatabase(ctx).give_atom(ctx.author, atom, amount)

    @remove.autocomplete("listing")
    async def removelisting_autocomplete(
        self, inter: discord.Interaction, current: int
    ):
        return [
            discord.app_commands.Choice(
                name=f"{shop['identity']}: {shop['amount']} {get_atomic_name(shop['atomid'])} for {shop['price']}",
                value=shop["identity"],
            )
            for shop in await ShopDatabase(
                await BuilderContext.from_interaction(inter)
            ).get_by_user(inter.user)
            if str(shop["identity"]) in str(current)
            or str(current) in str(shop["identity"])
        ]

    @shop.command()
    @describe(
        atom="Only view shops selling this atom", user="Only view shops by this user"
    )
    async def view(
        self, ctx: BuilderContext, atom: Optional[Atom], user: Optional[discord.User]
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
                vals = await db.get_with_attrs("atomid = $1", atom)
            vals = sorted(vals, key=lambda r: r["price"] / r["amount"])
            view = ShopView(ctx, vals, 10)
        else:
            if atom is None:
                vals = await db.get_by_user(user)
            else:
                vals = await db.get_with_attrs(
                    "atomid = $1 AND userid = $2", atom, user.id
                )
            vals = sorted(vals, key=lambda r: r["price"] / r["amount"])
            view = PersonalShopView(ctx, user, vals, 10)
        embed = await view.page_zero(ctx.interaction)
        await view.check_buttons()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @shop.command()
    async def info(self, ctx: BuilderContext, listing: Range[int, 1]):
        """
        Gets all available information about a shop posting.
        """
        shop: asyncpg.Record = await ShopDatabase(ctx).get_shop(listing)
        if shop is None:
            raise MissingShopEntry(
                "A shop with this ID does not exist. Maybe it was deleted, or you misspelled something."
            )

        embed = await format(
            ctx,
            desc=listing_information(shop),
        )
        view = PurchaseView(ctx, shop)
        message = await ctx.send(embed=embed, view=view)
        view.message = message


class ShopDatabase:
    def __init__(self, ctx: BuilderContext) -> None:
        self.ctx: BuilderContext = ctx
        self.apg: asyncpg.Connection = ctx.bot.apg

    async def getAll(self):
        command = """
            SELECT * FROM shops
        """
        return await self.apg.fetch(command)

    async def get_by_any(
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

    async def get_by_user(self, user: discord.User) -> List[asyncpg.Record]:
        command = """
            SELECT * FROM shops
            WHERE userid = $1
        """
        return await self.apg.fetch(command, user.id)

    async def delete(self, identity: int) -> asyncpg.Record:
        command = """
            DELETE FROM shops
            WHERE identity = $1
            RETURNING *
        """
        return await self.apg.fetchrow(command, identity)

    async def create(
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

    async def get_shop(self, identity: int):
        command = """
            SELECT * FROM shops
            WHERE identity = $1
        """
        return await self.apg.fetchrow(command, identity)

    async def remove(self, identity: int) -> List[asyncpg.Record]:
        command = """
            DELETE FROM shops
            WHERE identity = $1
            RETURNING *
        """
        return await self.apg.fetchrow(command, identity)

    async def get_with_attrs(self, wherestr: str, *args):
        command = f"""
            SELECT * FROM shops
            WHERE {wherestr}
        """
        return await self.apg.fetch(command, *args)


class ShopView(Paginator):
    def __init__(
        self,
        ctx: BuilderContext,
        values: Iterable,
        pagesize: int,
        *,
        timeout: Optional[float] = 45,
    ):
        super().__init__(ctx, values, pagesize, timeout=timeout)

    async def adjust(self, embed: discord.Embed):
        for shop in self.value_range:
            name = get_atomic_name(shop["atomid"])
            amt = shop["amount"]
            price = shop["price"]
            coin = Emojis.COIN_ID

            transid = shop["identity"]

            embed.add_field(
                name=f"`{name} [{amt}]` -> `{price}`{coin}",
                value=f"**Transaction ID:** `{transid}`",
                inline=False,
            )
        return embed

    async def embed(self, inter: discord.Interaction):
        embed = await format(self.ctx, title=f"Shops: Page `{self.position+1}` / `{self.maxpos+1}`")
        return embed


class PersonalShopView(Paginator):
    def __init__(
        self,
        ctx: BuilderContext,
        user: Union[discord.User, discord.Member],
        values: Iterable,
        pagesize: int,
        *,
        timeout: Optional[float] = 45,
    ):
        self.user = user
        super().__init__(ctx, values, pagesize, timeout=timeout)

    async def adjust(self, embed: discord.Embed):
        for shop in self.value_range:
            name = get_atomic_name(shop["atomid"])
            amt = shop["amount"]
            price = shop["price"]
            transid = shop["identity"]
            coin = Emojis.COIN_ID

            embed.add_field(
                name=f"`{name} [{amt}]` -> `{price}`{coin}",
                value=f"**Transaction ID:** `{transid}`",
            )
        return embed

    async def embed(self, inter: discord.Interaction):
        embed = await format(
            self.ctx,
            title=f"`{self.user}`'s Shops: Page `{self.position+1}` / `{self.maxpos+1}`",
        )
        return embed


class PurchaseView(BaseView):
    def __init__(
        self,
        ctx: BuilderContext,
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
            raise SelfAction("You cannot purchase your own shop!")
        rec = await ShopDatabase(self.ctx).remove(self.record["identity"])
        if rec is None:
            raise MissingShopEntry("This appears to already have been puchased. Sorry!")

        bdb: BalanceDatabase = BalanceDatabase(self.ctx)
        adb: AtomsDatabase = AtomsDatabase(self.ctx)
        if (price := rec["price"]) > (bal := await bdb.get_balance(self.ctx.author)):
            raise MissingFunds(f"Need {price:,}, have {bal:,}")

        new_balance = await bdb.add_to_balance(self.ctx.author, -price)
        atoms = await adb.give_atom(self.ctx.author, rec["atomid"], rec["amount"])
        atomname = get_atomic_name(atoms["atomid"])

        embed = await format(
            self.ctx,
            title="Shop Purchased!",
            desc=listing_information(rec)
            + f"\n**New balance:** `{new_balance:,}` [Before: `{bal:,}`{Emojis.COIN_ID}]\n**New Amount:** `{atomname}: {atoms['amount']}`",
        )

        await inter.response.send_message(embed=embed)
        self.message = await self.ctx.interaction.original_message()

    @discord.ui.button(
        label="Remove", emoji="\N{CROSS MARK}", style=discord.ButtonStyle.danger
    )
    async def destroy(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user.id != self.record["userid"]:
            raise Unowned("You cannot delete a shop that isn't yours!")
        result = await ShopDatabase(self.ctx).remove(self.record["identity"])
        if result is None:
            raise MissingShopEntry("Cannot find shop, it was most likely deleted.")
        else:
            embed = await format(
                self.ctx,
                title="Listing Successfully Removed",
                desc=listing_information(result),
            )
            await inter.response.send_message(embed=embed)


def listing_information(record: asyncpg.Record):
    atomname: str = get_atomic_name(record["atomid"])
    atom: int = record["atomid"]
    amount: int = record["amount"]
    price: int = record["price"]
    listingid: int = record["identity"]

    data = f"***__Listing Information__***\n**Atom:** `{atomname}` [ID: `{atom}`]\n**Amount:** `{amount:,}`\n**Price:** `{price:,}`{Emojis.COIN_ID}\n**Listing ID:** `{listingid}`"
    return data


async def setup(bot):
    await bot.add_cog(Shop(bot))
