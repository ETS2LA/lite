import src.settings as settings
import subprocess
import os

PATH = os.path.dirname(__file__).replace("src", "")

OS = os.name
with open(PATH + "version.txt") as f: VERSION = f.read()
REMOTE_VERSION = None
CHANGELOG = None

THEME = settings.Get("UI", "Theme", "dark")
BACKGROUND = None

FONT_SIZE = 11
TITLE_BAR_HEIGHT = 50
TEXT_COLOR = (255, 255, 255) if THEME == "dark" else (0, 0, 0)
BUTTON_COLOR = (42, 42, 42) if THEME == "dark" else (236, 236, 236)
BUTTON_HOVER_COLOR = (47, 47, 47) if THEME == "dark" else (231, 231, 231)
BUTTON_SELECTED_COLOR = (28, 28, 28) if THEME == "dark" else (250, 250, 250)
BUTTON_SELECTED_HOVER_COLOR = (28, 28, 28) if THEME == "dark" else (250, 250, 250)


TABS = ["Menu", "NavigationDetectionAI", "Settings"]
CANVAS_BOTTOM = settings.Get("UI", "Height", 400) - TITLE_BAR_HEIGHT - 1
CANVAS_RIGHT = settings.Get("UI", "Width", 700) - 1
CONTEXT_MENU = [False, 0, 0]
RENDER_FRAME = True
CACHED_FRAME = None
FRAME = None
ITEMS = []
AREAS = []

X = settings.Get("UI", "X", 0)
Y = settings.Get("UI", "Y", 0)
WIDTH = settings.Get("UI", "Width", 700)
HEIGHT = settings.Get("UI", "Height", 400)

HWND = None
PAGE = None
TAB = "Menu"
NAME = "ETS2LA-Lite"
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