from client_container import *

load_dotenv()

intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.listening, name=">>help")

bot: commands.Bot = discord.ext.commands.Bot(
    command_prefix=when_mentioned_or(">>",),
    case_insensitive=True,
    intents=intents,
    activity=activity,
    application_id="963411905018466314"
)

tree = bot.tree

async def load_extensions(logging = True):
        log = ""
        for cog in os.listdir("./cogs"):
            try:
                if cog.endswith(".py") and not cog.startswith("_"):
                    await bot.load_extension(f"cogs.{cog[:-3]}")
                    log += f"✅ {cog}\n" if logging else ""
                    
            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                await bot.load_extension(f"cogs.{cog[:-3]}")
                log += f"✅ {cog} [Reloaded]\n" if logging else ""

            except Exception as err:
                print(err)
                log += f"❌ {cog} [{err}]\n" if logging else ""
        print(log)


@bot.event
async def on_ready():
    print(f"Client online [User: {bot.user}, ID: {bot.user.id}]")


# Just a test to see if I can get slash commands working
@app_commands.command()
async def echo(interation: discord.Interaction, message: str):
    await interation.response.send_message(message, ephemeral=True)


async def main():
    await load_extensions()
    tree.add_command(echo, guild = bot.get_guild(871913539936329768))
    await bot.start(os.getenv("BOT_KEY"))


asyncio.run(main())