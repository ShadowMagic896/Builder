import asyncio
from asyncio.subprocess import Process
import os


async def snekbox_exec():
    # If creating contianer
    # os.system("docker run --ipc=none --privileged -p 8060:8060 -d ghcr.io/python-discord/snekbox")
    shell: Process = await asyncio.create_subprocess_shell("docker restart snekbox")
    await shell.communicate()
