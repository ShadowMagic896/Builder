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


class MissingShopEntry(BaseException):
    """
    Raised when a shop is not found, is but attempted to be acted upon.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class MissingFunds(BaseException):
    """
    Raised when a user doesn't have enough money for something.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class SelfAction(BaseException):
    """
    Raised when a user tries to do an invalid action on themselves.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class Unowned(BaseException):
    """
    Raised when a user tries to do an action on an unowned object.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)
