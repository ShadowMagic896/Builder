from settings import CATCH_ERRORS
from src.utils.subclass import BaseCog
from bot import Builder

from src.utils.error_funcs import (
    on_error,
    on_command_error,
    on_tree_error
)


class ErrorHandling(BaseCog):
    def __init__(self, bot: Builder) -> None:
        self.bot = bot
        if CATCH_ERRORS:
            self.bot.on_error = on_error
            self.bot.on_command_error = on_command_error
            self.bot.tree.on_error = on_tree_error



async def setup(bot):
    await bot.add_cog(ErrorHandling(bot))
