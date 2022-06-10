import os


async def beginDocker():
    command: str = "docker run --ipc=none --privileged -p 8060:8060 -d ghcr.io/python-discord/snekbox"
    os.system(command)  # Let PermissionError get raised
