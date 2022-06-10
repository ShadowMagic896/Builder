from discord.ext.commands import parameter
from src.utils import Converters


USER = parameter(default=lambda c: c.author, displayed_default=lambda c: str(c.author))
COLOR_CHANNEL_ALPHA = parameter(
    converter=Converters.ColorChannelConverterAlpha,
    default=lambda c: {0, 1, 2},
    displayed_default="R G B",
)
COLOR_CHANNEL_NO_ALPHA = parameter(
    converter=Converters.ColorChannelConverterNoAlpha,
    default=lambda c: {0, 1, 2},
    displayed_default="R G B",
)
