from typing import Set


class Const:
    class Emojis:
        COIN_ID = "<:Coin:972565900110745630>"
        BBARROW_ID = "<:BBArrow:971590922611601408>"
        BARROW_ID = "<:BArrow:971590903837913129>"
        FARROW_ID = "<:FArrow:971591003893006377>"
        FFARROW_ID = "<:FFArrow:971591109874704455>"

    class Cogs:
        FORBIDDEN_COGS: Set[str] = {
            "Dev",
            "Watchers",
            "Jishaku",
            "GUI",
            "InterHelp",
            "MixedHelp",
            "Help",
            "GitHub",
        }

        FORBIDDEN_GROUPS: Set[str] = {}

        FORBIDDEN_COMMANDS: Set[str] = {}

    class Rates:
        HOURLY = 1500
        DAILY = 7000
        WEEKLY = 50000

    class Paths:
        FONT = "C:/Windows/Fonts/"

    class URLs:
        REPO_URL: str = "https://github.com/ShadowMagic896/Builder/"
        ADVICE: str = "https://www.affirmations.dev/"
        AFFIRMATION: str = "https://api.adviceslip.com/advice/"
        QUIZ_API: str = "https://quizapi.io/api/v1/"
        RTD: str = "https://readthedocs.org/"
        RULE_34: str = "https://rule34.xxx/"
        NEKO_LIFE: str = "https://nekos.life/"
        NHENTAI: str = "https://nhentai.xxx/"
        NHENTAI_CDN: str = "https://cdn.nhentai.xxx/"
