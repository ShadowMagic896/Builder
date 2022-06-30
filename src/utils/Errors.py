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


class MissingCog(BaseException):
    """
    Raised when a user inputs an invalid cog.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class MissingCommand(BaseException):
    """
    Raised when a user inputs an invlid command.
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class ForbiddenData(BaseException):
    """
    Raised when a user tries to access forbidden commands or cogs
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class ContainerAlreadyRunning(BaseException):
    """
    Raised when a user tries to create a new container, but one is already running
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class ScopeError(BaseException):
    """
    Raised when a user tries to run a command in the incorrect place
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class SessionInProgress(BaseException):
    """
    Raised when a user tries to run eval when they already have a session in progress
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class NoDocumentsFound(BaseException):
    """
    Raised when no results for a RTFM search are found
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)


class Fatal(BaseException):
    """
    Raised when a fatal internal exception occurs
    """

    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)
