from dotenv import load_dotenv
from client_container import *
from _aux.extensions import *

load_dotenv()

intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.listening, name=">>help")


bot = discord.ext.commands.Bot(
    command_prefix=when_mentioned_or(">>",),
    case_insensitive=True,
    intents=intents,
    activity=activity,
)

async def main():
    await load_extensions(bot, True)
    await bot.start(os.getenv("BOT_KEY"))

asyncio.run(main())