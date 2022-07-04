import aiohttp
import logging
from environ import BOT_KEY
from src.utils.bot_types import Builder
from src.utils.errors import Fatal
from src.utils.startup import prepare, start


if __name__ == "__main__":

    async def main() -> None:
        bot: Builder = Builder()
        bot: Builder = await prepare(bot)
        try:
            await bot.start(BOT_KEY)
        except aiohttp.ClientConnectionError as err:
            msg: str = "Could not locate host"
            logging.fatal(msg)
            await bot.session.close()
            raise Fatal(msg) from err

    start(main)
