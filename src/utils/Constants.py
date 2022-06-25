from typing import Set, Final, final

@final
class Emojis:
    COIN_ID: Final[str] = "<:Coin:972565900110745630>"
    BBARROW_ID: Final[str] = "<:BBArrow:971590922611601408>"
    BARROW_ID: Final[str] = "<:BArrow:971590903837913129>"
    FARROW_ID: Final[str] = "<:FArrow:971591003893006377>"
    FFARROW_ID: Final[str] = "<:FFArrow:971591109874704455>"

@final
class Cogs:
    FORBIDDEN_COGS: Final[Set[str]] = {
        "Dev",
        "Watchers",
        "Jishaku",
        "GUI",
        "InterHelp",
        "MixedHelp",
        "Help",
        "GitHub",
    }

    FORBIDDEN_GROUPS: Final[Set[str]] = {}

    FORBIDDEN_COMMANDS: Final[Set[str]] = {}

@final
class Rates:
    HOURLY: Final[int] = 1500
    DAILY: Final[int] = 7000
    WEEKLY: Final[int] = 50000

@final
class Paths:
    FONT: Final[str] = "C:/Windows/Fonts/"

@final
class URLs:
    REPO: Final[str] = "https://github.com/ShadowMagic896/Builder"
    AFFIRMATION_API: Final[str] = "https://www.affirmations.dev"
    ADVICE_API: Final[str] = "https://api.adviceslip.com/advice" # For some reason the API cares about the trailing slash
    DOG_API: Final[str] = "https://dog.ceo/api/breeds/image/random"
    CAT_API: Final[str] = "https://cataas.com"
    FOX_API: Final[str] = "https://randomfox.ca/floof"
    DUCK_API: Final[str] = "https://random-d.uk/api/random"  
    QUIZ_API: Final[str] = "https://quizapi.io/api/v1/questions"
    LIBRARY_API: Final[str] = "https://libraries.io/api"
    RTD: Final[str] = "https://readthedocs.org"


    RULE_34: Final[str] = "https://rule34.xxx/"
    NEKO_LIFE: Final[str] = "https://nekos.life/"
    NHENTAI: Final[str] = "https://nhentai.xxx/"
    NHENTAI_CDN: Final[str] = "https://cdn.nhentai.xxx/"
    PORNHUB: Final[str] = "https://pornhub.com/"

@final
class Timers:
    RTFM_CACHE_CLEAR: Final[float] = 120.0
