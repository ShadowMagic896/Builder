from client_container import *
# import sys
load_dotenv()

intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.listening, name=">>help")

# def func():
#     print(also_a_func())
# def also_a_func():
#     return "something"
# func()
# sys.exit()

bot = discord.ext.commands.Bot(
    command_prefix=when_mentioned_or(">>",),
    case_insensitive=True,
    intents=intents,
    activity=activity
)

# Load all initial cogs
async def load_extensions():
    for cog in os.listdir("./cogs"):
        try:
            if cog.endswith(".py") and not cog.startswith("_"):
                await bot.load_extension(f"cogs.{cog[:-3]}")
                print(f"Loaded file: \"{cog}\"")
        except Exception as err:
            print(f"Cannot load file: \"{cog}\" [{err}]")

# @bot.command()
# async def load(ctx, cog="*", log_level = 0):
#     if cog != "*":
#         try:
#             await bot.

@bot.event
async def on_ready():
    print(f"Client online [User: {bot.user}, ID: {bot.user.id}]")

async def main():
    await load_extensions()
    await bot.start(os.getenv("BOT_KEY"))

asyncio.run(main())