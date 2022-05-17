from typing import Any


class InternalError(BaseException):
    def __init__(self, error: Any, *args: object) -> None:
        super().__init__(error, *args)
