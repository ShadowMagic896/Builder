"""
Runs a small script to install all requirements
"""
import sys

import os


ask_for_install: bool = False
ver = sys.version_info
print(f"Running with Python: {sys.version} ")
if float(f"{ver.major}.{ver.minor}") < 3.10:
    raise TypeError(
        "Python version is not >=3.10\nPlease see https://www.python.org/downloads/ to get the latest download"
    )
cpath: str = str(os.getcwd()).lower().strip("/\\")
command: str = ""
if not cpath.endswith("builder"):
    raise IOError("Working directory must builder")
if (
    ask_for_install
    and input(
        "Install Required Modules? (Required for first-time use) (Y/N)\n  | "
    ).lower()
    == "y"
):
    command += "py reqs/requirements.py && py -m pip install -Ur reqs/requirements.txt"
    os.system(command)
    response = input(
        "\nINSTALLATIONS COMPLETE\nContinue and run bot? (Y/N)\n  | "
    ).lower()
    if response == "y":
        os.system("py bot.py")
else:
    os.system("py bot.py")
