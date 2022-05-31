from enum import Enum


class CONSTANTS:
    class Emojis:
        def __init__(self):
            self.COIN_ID = "<:Coin:972565900110745630>"
            self.BBARROW_ID = "<:BBArrow:971590922611601408>"
            self.BARROW_ID = "<:BArrow:971590903837913129>"
            self.FARROW_ID = "<:FArrow:971591003893006377>"
            self.FFARROW_ID = "<:FFArrow:971591109874704455>"

    class Cogs:
        def __init__(self) -> None:
            self.FORBIDDEN_COGS = {
                "Dev",
                "Watchers",
                "Jishaku",
                "GUI",
                "InterHelp",
                "MixedHelp",
                "Help",
                "GitHub",
            }

    class Rates:
        def __init__(self) -> None:
            self.HOURLY = 1500
            self.DAILY = 7000
            self.WEEKLY = 50000

    class Paths:
        def __init__(self) -> None:
            self.FONT = "C:/Windows/Fonts/"
