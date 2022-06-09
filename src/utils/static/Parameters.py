from discord.ext.commands import parameter
from src.utils import Converters


USER = parameter(default=lambda c: c.author, displayed_default=lambda c: str(c.author))
COLOR_CHANNEL_ALPHA = parameter(
    converter=Converters.ColorChannelConverterAlpha,
    default=lambda c: "RGB",
    displayed_default=lambda c: "RGB",
)
COLOR_CHANNEL_NO_ALPHA = parameter(
    converter=Converters.ColorChannelConverterNoAlpha,
    default=lambda c: "RGB",
    displayed_default=lambda c: "RGB",
)
