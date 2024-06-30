import subprocess
import os

PATH = os.path.dirname(__file__).replace("src", "")

OS = os.name
with open(PATH + "version.txt") as f: VERSION = f.read()

ROOT = None
HWND = None
BREAK = False

CONSOLENAME = None
CONSOLEHWND = None

try:
    try:
        LASTUPDATE = subprocess.check_output("git log -1 --date=local --format=%cd", shell=True).decode("utf-8").replace("\n", "")
    except:
        unixPath = PATH.replace("\\", "/")
        if unixPath[-1] == "/":
            unixPath = unixPath[:-1]
        os.system(f'cmd /k "cd {PATH} & git config --global --add safe.directory {unixPath} & exit"')
        LASTUPDATE = subprocess.check_output("git log -1 --date=local --format=%cd", shell=True).decode("utf-8").replace("\n", "")
except:
    LASTUPDATE = "Unknown"