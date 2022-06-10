import asyncio
from typing import Tuple


async def snekboxExec():
    # If creating contianer
    # os.system("docker run --ipc=none --privileged -p 8060:8060 -d ghcr.io/python-discord/snekbox")
    command: str = "docker restart snekbox"
    shell = await asyncio.create_subprocess_shell(command)
    result: Tuple[bytes, bytes] = await shell.communicate()
    print(result)
