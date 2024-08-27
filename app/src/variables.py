import src.settings as settings
import os

PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__))).replace("\\", "/") + "/"

OS = os.name
with open(PATH + "config/version.txt") as f: VERSION = f.read()
REMOTE_VERSION = None
CHANGELOG = None
USERCOUNT = 0

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
CONTEXT_MENU_ITEMS = []
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