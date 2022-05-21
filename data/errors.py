from typing import Any


class InternalError(BaseException):
    """
    To be raised when an error occurs within the bot.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class TooManyArguments(BaseException):
    """
    Raised internally for when too many kwargs are speficied for a method.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class MissingArguments(BaseException):
    """
    Raised internally for when not enough kwargs are speficied for a method.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)
