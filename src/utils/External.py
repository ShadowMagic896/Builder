import asyncio
from asyncio.subprocess import Process
import logging
import os

import aiofiles
import ctypes

import psutil

from data.Settings import DOCKER_DESKTOP_LOCATION


async def snekbox_exec():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise PermissionError("Not running in administrator")
    if not "Docker Desktop.exe" in (i.name() for i in psutil.process_iter()):
        print("Starting Docker Desktop")
        os.startfile(DOCKER_DESKTOP_LOCATION)
        await asyncio.sleep(5)
    shell: Process = await asyncio.create_subprocess_shell(
        f"docker restart snekbox >> ./data/logs/docker.log"
    )
    await shell.communicate()
