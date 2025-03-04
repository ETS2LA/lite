import src.settings as settings
import os

OS = os.name
Path = os.path.dirname(os.path.dirname(os.path.dirname(__file__))).replace("\\", "/") + "/"
with open(f"{Path}config/version.txt") as File: Version = File.read()
RemoteVersion = None
Changelog = None
UserCount = "Loading"

Language = settings.Get("UI", "Language", "English")
Theme = settings.Get("UI", "Theme", "Dark")
DevelopmentMode = False
Background = None

Queue = []
Locks = {}
SharedMemories = {}
PluginProcesses = {}
SharedMemorySize = 1024
AvailablePlugins = [Plugin for Plugin in os.listdir(f"{Path}app/plugins")]
CUDAAvailable = False
CUDAInstalled = False
CUDACompatible = False
CUDADetails = None

ETS2Path = ""
ATSPath = ""

Popup = [None, 0, 0.5]
Data = {}
FOV = 80

WindowX = settings.Get("UI", "X", 100)
WindowY = settings.Get("UI", "Y", 100)
WindowWidth = settings.Get("UI", "Width", 700)
WindowHeight = settings.Get("UI", "Height", 400)

Name = "ETS2LA-Lite"
Page = settings.Get("UI", "Page", "Menu")
Frame = None
Break = False

ConsoleName = None
ConsoleHWND = None


TabButtonColor = (47, 47, 47) if Theme == "Dark" else (231, 231, 231)
TabButtonHoverColor = (41, 41, 41) if Theme == "Dark" else (244, 244, 244)
TabButtonSelectedColor = (28, 28, 28) if Theme == "Dark" else (250, 250, 250)
TabButtonSelectedHoverColor = (28, 28, 28) if Theme == "Dark" else (250, 250, 250)