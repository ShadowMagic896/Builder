import discord
from discord.ext import commands
from discord.ext.commands import Context

import re

class UserConverter(commands.Converter):
    async def convert(self, ctx: Context, user: str):
        if not user:
            raise commands.errors.UserNotFound(user)
        _id = None
        if user.startswith("<@"):  # User is a mention
            try:
                _id = int(str(user)[2:-1])
            except ValueError:
                raise commands.errors.UserNotFound(user)
        else:  # It is a user ID
            try:
                _id = int(user)  # Just an ID
            except ValueError:
                for m in ctx.guild.members:  # Try to catch a name
                    if m.name == user or "{}#{}".format(
                            m.name, m.discriminator) == user:
                        _id = m.id
                else:
                    commands.errors.UserNotFound(user)
        try:
            users = []
            for r in ctx.bot.guilds:
                for m in r.members:
                    users.append(m)

            return discord.utils.find(lambda u: u.id == _id, users)
        except discord.errors.NotFound:
            raise commands.errors.UserNotFound(user)

class YouTubeLink(commands.Converter):
    async def convert(self, ctx: Context, arg: str):
        match = "(http(s)?://)?(www.)?youtube.com/watch\?v=.+"

        if not re.match(match, arg):
            raise commands.errors.BadArgument("Invalid URL")

        if not arg.startswith("https://"):
            arg = "https://" + arg

        arg = arg.replace("www.", "")

        if not re.match(match, arg):
            raise commands.errors.BadArgument("Invalid URL: %s" % arg)

        return arg