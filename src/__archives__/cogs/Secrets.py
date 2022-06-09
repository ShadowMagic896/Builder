import functools
from typing import List
import discord
from discord import app_commands
from discord.app_commands import Range, describe
from discord.ext import commands

import functools

import morse_code

from src.ext.Embeds import fmte


class Secrets(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

        self.u_alphas: List[str] = [chr(i) for i in range(65, 91)]
        self.l_alphas: List[str] = [chr(i) for i in range(97, 123)]
        self.digits: List[str] = [str(i) for i in range(0, 10)]

        async def en_template(ctx, name: str, result):
            embed = fmte(
                ctx,
                t=f"Encoding Complete\nMethod: `{name.capitalize()}`",
                d=f"```\n{result}\n```",
            )
            await ctx.send(embed=embed)

        async def de_template(ctx, name: str, result):
            embed = fmte(
                ctx, t=f"Decoding Complete\nMethod: `{name}`", d=f"```\n{result}\n```"
            )
            await ctx.send(embed=embed)

        # self.encoding_methods = {
        #     "shift": self._shift,
        #     "morse": self._morse_encode
        # }

        # self.decoding_methods = {
        #     "shift": self._shift,
        #     "morse": self._morse_decode
        # }

        # for name, func in list(self.encoding_methods.items()):
        #     commands.HybridCommand()
        #     await self.bot.add_command(
        #         command
        #     )
        #     @self.encode.command(name=name)
        #     async def __template__(self, ctx: commands.Context)

    def ge(self):
        return "\N{CLOSED LOCK WITH KEY}"

    async def _shift(self, msg: str, amt: int):
        new_string: str = ""
        for ch in msg:
            if not ch.isalnum():
                new_string += ch
                continue
            srch: list = None
            if ch.isdigit():
                srch = self.digits
            elif ch.isupper():
                srch = self.u_alphas
            else:
                srch = self.l_alphas
            new_string += srch[(srch.index(ch) + amt) % len(srch)]
        return new_string

    async def _morse_encode(self, msg: str):
        enc = morse_code.encrypt(msg)
        if not enc:
            raise ValueError("Cannot encrypt this message.")
        return enc

    async def _morse_decode(self, msg: str):
        dec = morse_code.decrypt(msg)
        if not dec:
            raise ValueError("Cannot decrypt this message.")
        return dec

    @commands.hybrid_group()
    async def encode(self, ctx: commands.Context):
        pass

    @encode.command()
    @describe(
        message="The message to encrypt", shifts="How many characters to shift by"
    )
    async def shift(self, ctx: commands.Context, message: str, shifts: int):
        """
        Encodes a message by shifting characters in the alphabet. Also known as Caesarean shifting.
        """
        encoded: str = await self._shift(message, shifts)
        embed = fmte(
            ctx, t="Encoding Complete\nMethod: `Shift`", d=f"```\n{encoded}\n```"
        )
        await ctx.send(embed=embed)

    @encode.command()
    @describe(
        message="The message to encrypt",
    )
    async def morse(self, ctx: commands.Context, message: str):
        """
        Encodes a message by to a series of dots and dashes.
        """
        encoded: str = await self._morse_encode(message)
        embed = fmte(
            ctx, t=f"Encoding Complete\nMethod: `Morse`", d=f"```\n{encoded}\n```"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_group()
    async def decode(self, ctx: commands.Context):
        pass

    @decode.command()
    @describe(
        message="The message to dncrypt", shifts="How many characters to shift by"
    )
    async def shift(self, ctx: commands.Context, message: str, shifts: int):
        """
        Decodes a message by shifting characters in the alphabet. Also known as Caesarean shifting.
        """
        encoded: str = await self._shift(message, -shifts)
        embed = fmte(
            ctx, t="Decoding Complete\nMethod: `Shift`", d=f"```\n{encoded}\n```"
        )
        await ctx.send(embed=embed)

    @decode.command()
    @describe(
        message="The message to decrypt",
    )
    async def morse(self, ctx: commands.Context, message: str):
        """
        Decodes a message by to a series of dots and dashes.
        """
        encoded: str = await self._morse_decode(message)
        embed = fmte(
            ctx, t=f"Decoding Complete\nMethod: `Morse`", d=f"```\n{encoded}\n```"
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Secrets(bot))
