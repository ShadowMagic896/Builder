import asyncpg
import discord
from asyncpg import Connection, Record
from chempy.util import periodic
from discord.app_commands import describe
from discord.ext import commands
from discord.ext.commands import parameter
from typing import List, Optional, Union

from ..utils.bot_types import Builder, BuilderContext
from ..utils.converters import Atom

from ..utils.item_maps import Chemistry, get_atomic_name
from ..utils.subclass import BaseCog, Paginator


chem = Chemistry()


class Atoms(BaseCog):
    """
    Gather random atoms!
    """

    def ge(self):
        return "\N{ATOM SYMBOL}"

    @commands.hybrid_group()
    async def atoms(self, ctx: BuilderContext):
        pass

    # @atoms.command()
    # @commands.is_owner()
    # async def run(self, ctx: BuilderContext, command: str, mode: str = "fetch"):
    #     return await ctx.send(
    #         str(await getattr(self.bot.apg, mode, "fetch")(command))[:2000]
    #     )

    @atoms.command()
    @describe(atom="The atoms to give. Can be a full name, symbol, or atomic number.")
    async def give(
        self,
        ctx: BuilderContext,
        atom: Atom,
        amount: int,
        user: Optional[discord.User] = parameter(
            default=lambda c: c.author, displayed_default=lambda c: str(c.author)
        ),
    ):
        """
        Magically creates atoms and gives them to a user.
        """
        atomname = periodic.names[atom - 1]
        old = await AtomsDatabase(ctx).get_atoms(user)
        old_amount = (
            [v for v in old if v["atomid"] == atom][0]["count"] if len(old) != 0 else 0
        )
        await AtomsDatabase(ctx).give_atom(user, atom, amount)
        embed = await ctx.format(
            title=f"Resources Given to `{user}`",
            desc=f"**Resource Name:** `{atomname}`\n**Resource ID:** `{atom}`\n**Old Amount:** `{old_amount:,}`\n**New Amount:** `{max(old_amount+amount, 0):,}`",
        )
        await ctx.send(embed=embed)

    @atoms.command()
    async def all(self, ctx: BuilderContext):
        """
        Shows a list of all atoms you can get.
        """
        values: List[Record] = await AtomsDatabase(ctx).allatoms()

        view = AtomsView(ctx, values=values, title="All Atoms", sort="atomid")
        embed = await view.page_zero(ctx.interaction)
        await view.check_buttons()

        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @atoms.command()
    @discord.app_commands.choices(
        sort=[
            discord.app_commands.Choice(name=x, value=y)
            for x, y in [
                ("By ID", "atomid"),
                ("By name", "name"),
                ("By amount", "count"),
            ]
        ]
    )
    @describe(user="Whose atoms to view", sort="How to sort the data")
    async def view(
        self,
        ctx: BuilderContext,
        user: Optional[discord.User] = parameter(
            default=lambda c: c.author, displayed_default=lambda c: str(c.author)
        ),
        sort: Optional[str] = "atomid",
    ):
        """
        Shows all atoms that a user has.
        """
        values: Union[List[Record], List] = await AtomsDatabase(ctx).get_atoms(user)
        view = AtomsView(ctx, values=values, title=f"`{user}`'s Atoms", sort=sort)
        embed = await view.page_zero(ctx.interaction)
        await view.check_buttons()

        message = await ctx.send(embed=embed, view=view)
        view.message = message


class AtomsDatabase:
    def __init__(self, ctx: BuilderContext):
        self.bot: Builder = ctx.bot
        self.apg: Connection = self.bot.apg

    async def get_atoms(
        self, user: Union[discord.Member, discord.User]
    ) -> List[asyncpg.Record]:
        await self.register_user(user)
        command = """
            SELECT *
            FROM inventories
                JOIN atoms
                    USING(atomid)
            WHERE userid = $1
        """
        return await self.apg.fetch(command, user.id)

    async def give_atom(
        self, user: Union[discord.Member, discord.User], atomid: int, amount: int
    ) -> asyncpg.Record:
        await self.register_user(user)
        command = """
            INSERT INTO inventories
            VALUES (
                $1::BIGINT,
                $2::INTEGER,
                $3::INTEGER
            )
            ON CONFLICT(userid, atomid) DO UPDATE
            SET count = inventories.count + $3
            RETURNING *
        """
        try:
            return await self.apg.execute(command, user.id, atomid, amount)
        except asyncpg.CheckViolationError as checkError:
            # The amount is negative
            command = """
                SELECT *
                FROM inventories
                WHERE userid = $1
            """
            current_amt = (await self.apg.fetchrow(command, user.id))["count"]
            requested_amt = int(str(checkError).split()[-1][:-2]) * -1

            if current_amt > requested_amt:
                command = """
                    UPDATE inventories
                    SET count = $1
                    WHERE userid = $2
                        AND atomid = $3
                """
                await self.apg.execute(
                    command, current_amt - requested_amt, user.id, atomid
                )
            else:
                command = """
                    DELETE FROM inventories
                    WHERE userid = $1
                        AND atomid = $2
                """
                await self.apg.execute(command, user.id, atomid)

    async def create_atom(
        self, name: str, description: Optional[str] = "No Description"
    ) -> asyncpg.Record:
        """
        Adds an atom to the database. Returns the status of the command.
        """
        command = """
            INSERT INTO atoms(name, description)
            VALUES (
                $1::TEXT,
                $2::TEXT
            )
            RETURNING
        """
        return await self.apg.fetchrow(command, name, description)

    async def get_atom(
        self,
        *,
        atom: Optional[str] = None,
    ) -> Optional[asyncpg.Record]:
        command = f"""
            SELECT *
            FROM atoms
            WHERE name = $1
        """
        result = await self.apg.fetchrow(command, get_atomic_name(atom))
        return result

    async def register_user(self, user: discord.User):
        command = """
            INSERT INTO users(userid)
            VALUES (
                $1
            )
            ON CONFLICT DO NOTHING
        """
        await self.apg.execute(command, user.id)

    async def allatoms(self):
        return await self.apg.fetch("SELECT * FROM atoms")


class AtomsView(Paginator):
    def __init__(
        self,
        ctx: BuilderContext,
        *,
        values: List[Record],
        title: str,
        sort: str = "id",
    ):
        values = sorted(values, key=lambda x: x[sort])
        self.title = title
        super().__init__(ctx, values, 5)

    async def adjust(self, embed: discord.Embed):
        for value in self.value_range:
            try:
                name = f"{value['name']}: `{value['count']:,}`"
            except KeyError:
                name = value["name"]
            embed.add_field(
                name=name,
                value=value["description"],
                inline=False,
            )
        return embed

    async def embed(self, inter: discord.Interaction):
        embed = await self.ctx.format(
            title=f"{self.title}: Page `{self.position+1}` / `{self.maxpos+1}`",
        )
        return embed


async def setup(bot):
    await bot.add_cog(Atoms(bot))
