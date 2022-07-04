from discord.ext.commands import parameter

from .. import converters


USER = parameter(default=lambda c: c.author, displayed_default=lambda c: str(c.author))
COLOR_CHANNEL_ALPHA = parameter(
    converter=converters.ColorChannelConverterAlpha,
    default=lambda c: {0, 1, 2},
    displayed_default="R G B",
)
COLOR_CHANNEL_NO_ALPHA = parameter(
    converter=converters.ColorChannelConverterNoAlpha,
    default=lambda c: {0, 1, 2},
    displayed_default="R G B",
)
