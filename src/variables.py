import os

PATH = os.path.dirname(__file__).replace("src", "")

OS = os.name
with open(PATH + "version.txt") as f: VERSION = f.read()

ROOT = None
HWND = None
BREAK = False

CONSOLENAME = None
CONSOLEHWND = None