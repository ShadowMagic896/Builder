class InternalError(BaseException):
    """
    To be raised when an error occurs within the bot.
    """


class TooManyArguments(BaseException):
    """
    Raised internally for when too many kwargs are speficied for a method.
    """


class MissingArguments(BaseException):
    """
    Raised internally for when not enough kwargs are speficied for a method.
    """


class MissingShopEntry(BaseException):
    """
    Raised when a shop is not found, is but attempted to be acted upon.
    """


class MissingFunds(BaseException):
    """
    Raised when a user doesn't have enough money for something.
    """


class SelfAction(BaseException):
    """
    Raised when a user tries to do an invalid action on themselves.
    """


class Unowned(BaseException):
    """
    Raised when a user tries to do an action on an unowned object.
    """


class MissingCog(BaseException):
    """
    Raised when a user inputs an invalid cog.
    """


class MissingGroup(BaseException):
    """
    Raised when a user inputs an invalid group.
    """


class MissingCommand(BaseException):
    """
    Raised when a user inputs an invlid command.
    """


class ForbiddenData(BaseException):
    """
    Raised when a user tries to access forbidden commands or cogs
    """


class ContainerAlreadyRunning(BaseException):
    """
    Raised when a user tries to create a new container, but one is already running
    """


class ScopeError(BaseException):
    """
    Raised when a user tries to run a command in the incorrect place
    """


class SessionInProgress(BaseException):
    """
    Raised when a user tries to run eval when they already have a session in progress
    """


class NoDocumentsFound(BaseException):
    """
    Raised when no results for a RTFM search are found
    """


class Fatal(BaseException):
    """
    Raised when a fatal internal exception occurs
    """
