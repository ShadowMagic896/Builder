import asyncio
import functools
import logging
from typing import Any, Callable


async def run(func: Callable, *args, **kwargs) -> Any:
    if not callable(func):
        if args and callable(args[0]):
            logging.error("Remove loop argument from coro.run")
            args = list(args)
            func = args.pop(0)
    part = functools.partial(func, *args, **kwargs)
    return await asyncio.get_event_loop().run_in_executor(None, part)
