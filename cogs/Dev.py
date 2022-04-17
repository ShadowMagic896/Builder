from client_container import *

class Dev(commands.Cog):
    """
    This cog is for any commands that help users find information about other users, this bot, the server, etc.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.hybrid_group(aliases = ["devs", "developers", "team", "owners"])
    async def dev(self, ctx):
        app = (await self.bot.application_info())
        img = app
        embed = fmte(
            ctx,
            t = "Hello! I'm {}.".format(self.bot.user.display_name),
            d = "Devs on **{}**:\n{}".format(app.team.name, "\n".join(["**{}#{}**".format(member.name, member.discriminator) for member in app.team.members]))
        )
        embed.set_image(url=app.team.icon)

        await ctx.send(embed=embed)
        
    @dev.command()
    @commands.is_owner()
    async def load(self, ctx, cog: str = "*", logging: bool = True):
        log = ""
        if cog == "*":
            for cog in os.listdir("./cogs"):
                
                if cog.endswith(".py") and not cog.startswith("_"):
                    try:
                        await self.bot.load_extension(f"cogs.{cog[:-3]}")
                        log += f"✅ {cog}\n"
                            
                    except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                        await self.bot.reload_extension(f"cogs.{cog[:-3]}")
                        log += f"✅ {cog}\n"

                    except Exception as err:
                        print(err)
                        log += f"❌ {cog} [{err}]\n"
        if logging: await ctx.send(log, ephemeral = True)
    
    
    @dev.command()
    @commands.is_owner()
    async def sync(self, ctx: Context, guilds: Greedy[int], spec: str = None) -> None:
        """
        [Owner only] Syncs all commands.
        Usage: >>sync [guilds_ids*] [spec: str]
        """
        if not guilds:
            if spec == "*":
                fmt = await ctx.bot.tree.sync(guild=ctx.guild)
            else:
                fmt = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(fmt)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        fmt = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                fmt += 1
        await load_extensions(logging=True)
        await ctx.send(f"Synced the tree to {fmt}/{len(guilds)} guilds.")
    
    @dev.command()
    @commands.is_owner()
    async def rectest(self, ctx: commands.Context):
        discord.cate
        pass
        
async def setup(bot):
    await bot.add_cog(Dev(bot))