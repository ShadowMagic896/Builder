import asyncio
import functools
from typing import Any, Callable


async def run(func: Callable, *args, **kwargs) -> Any:
    part = functools.partial(func, *args, **kwargs)
    return await asyncio.get_event_loop().run_in_executor(None, part)
