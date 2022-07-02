import asyncio
import ctypes
import os
import psutil
from asyncio.subprocess import Process
from settings import DOCKER_DESKTOP_LOCATION


async def snekbox_exec():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise PermissionError("Not running in administrator")
    if "Docker Desktop.exe" not in (i.name() for i in psutil.process_iter()):
        print("Starting Docker Desktop")
        os.startfile(DOCKER_DESKTOP_LOCATION)
        await asyncio.sleep(5)
    shell: Process = await asyncio.create_subprocess_shell(
        f"docker restart snekbox >> ./data/logs/docker.log"
    )
    await shell.communicate()
