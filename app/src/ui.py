import src.variables as variables
import src.settings as settings
import src.console as console
import src.plugins as plugins
import src.pytorch as pytorch
import src.updater as updater
import src.server as server
import src.setup as setup

import multiprocessing
import SimpleWindow
import numpy as np
import subprocess
import webbrowser
import threading
import keyboard
import ImageUI
import cv2


AvailableLanguages = list(ImageUI.Translations.GetAvailableLanguages().keys())
EnabledPlugins = {Plugin: settings.Get("Plugins", Plugin, False) for Plugin in variables.AvailablePlugins}
HideConsoleSwitch = settings.Get("Console", "HideConsole", False)
SendCrashReportsSwitch = settings.Get("CrashReports", "SendCrashReports") == True
EnableDisableKey = settings.Get("Controls", "Steering", "n")
ShowContextMenu = False


def EnableDisableKeyCallback(Input):
    Valid = True
    try:
        keyboard.is_pressed(Input)
    except:
        Valid = False
    if len(Input) != 1:
        Valid = False
    Top = 0
    Left = 0
    Right = variables.WindowWidth - 1
    if Valid == False:
        ImageUI.Popup(Text="Invalid Key!",
                      StartX1=Left + 10 - Right / 4,
                      StartY1=Top + 270,
                      StartX2=Left + 0,
                      StartY2=Top + 300,
                      EndX1=Left + 10,
                      EndY1=Top + 270,
                      EndX2=Right / 4,
                      EndY2=Top + 300,
                      ID="EnableDisableKey",
                      ShowDuration=1.5)
    else:
        ImageUI.Popup(Text="Key Updated!",
                      StartX1=Left + 10 - Right / 4,
                      StartY1=Top + 270,
                      StartX2=Left + 0,
                      StartY2=Top + 300,
                      EndX1=Left + 10,
                      EndY1=Top + 270,
                      EndX2=Right / 4,
                      EndY2=Top + 300,
                      ID="EnableDisableKey",
                      ShowDuration=1.5)
        if settings.Get("Controls", "Steering", "n") != Input:
            settings.Set("Controls", "Steering", Input)
            plugins.ManagePlugins(Plugin="All", Action="Restart")


def Initialize():
    WindowWidth = settings.Get("UI", "Width", 700)
    WindowHeight = settings.Get("UI", "Height", 400)
    WindowX = settings.Get("UI", "X", 100)
    WindowY = settings.Get("UI", "Y", 100)

    if WindowWidth < 50 or WindowHeight < 50:
        settings.Set("UI", "Width", 700)
        settings.Set("UI", "Height", 400)
        WindowWidth = 700
        WindowHeight = 400

    variables.Background = np.zeros((WindowHeight, WindowWidth, 3), np.uint8)
    variables.Background[:] = (28, 28, 28) if variables.Theme == "Dark" else (250, 250, 250)
    cv2.rectangle(variables.Background, (0, 0), (WindowWidth - 1, 49), (47, 47, 47) if variables.Theme == "Dark" else (231, 231, 231), -1)

    SimpleWindow.Initialize(Name=variables.Name,
                            Size=(WindowWidth, WindowHeight),
                            Position=(WindowX, WindowY),
                            TitleBarColor=(47, 47, 47) if variables.Theme == "Dark" else (231, 231, 231),
                            Resizable=False,
                            TopMost=False,
                            Undestroyable=False,
                            Icon=f"{variables.Path}app/assets/favicon.ico")

    SimpleWindow.Show(variables.Name, variables.Background)

    ImageUI.Settings.PopupShowDuration = 3
    ImageUI.Settings.CachePath = f"{variables.Path}cache"

    ImageUI.SetTranslator(SourceLanguage="English", DestinationLanguage=variables.Language)
    ImageUI.SetTheme(variables.Theme)
    Update()


def SetTheme(Theme):
    settings.Set("UI", "Theme", Theme)
    variables.Theme = Theme
    variables.Background = np.zeros((variables.WindowHeight, variables.WindowWidth, 3), np.uint8)
    variables.Background[:] = (28, 28, 28) if variables.Theme == "Dark" else (250, 250, 250)
    cv2.rectangle(variables.Background, (0, 0), (variables.WindowWidth - 1, 49), (47, 47, 47) if variables.Theme == "Dark" else (231, 231, 231), -1)
    ImageUI.SetTheme(Theme)
    SimpleWindow.SetTitleBarColor(variables.Name, (47, 47, 47) if variables.Theme == "Dark" else (231, 231, 231))


def Popup(Text, Progress = 0):
    if multiprocessing.current_process().name != "MainProcess":
        plugins.AddToQueue({"Popup": [Text, Progress]})
        return
    Right = variables.WindowWidth - 1
    Bottom = variables.WindowHeight - 1
    ImageUI.Popup(Text,
                  StartX1=Right * 0.3,
                  StartY1=Bottom,
                  StartX2=Right * 0.7,
                  StartY2=Bottom + 20,
                  EndX1=Right * 0.2,
                  EndY1=Bottom - 50,
                  EndX2=Right * 0.8,
                  EndY2=Bottom - 10,
                  ID="MainPopup",
                  Progress=Progress)


def Resize(WindowX, WindowY, WindowWidth, WindowHeight):
    variables.WindowX = WindowX
    variables.WindowY = WindowY
    variables.WindowWidth = WindowWidth
    variables.WindowHeight = WindowHeight
    variables.Background = np.zeros((WindowHeight, WindowWidth, 3), np.uint8)
    variables.Background[:] = (28, 28, 28) if variables.Theme == "Dark" else (250, 250, 250)
    cv2.rectangle(variables.Background, (0, 0), (WindowWidth - 1, 49), (47, 47, 47) if variables.Theme == "Dark" else (231, 231, 231), -1)


def Restart():
    if variables.DevelopmentMode == True:
        subprocess.Popen(f"python {variables.Path}app/main.py --dev", cwd=variables.Path)
    else:
        subprocess.Popen(f"{variables.Path}Start.bat", cwd=variables.Path, creationflags=subprocess.CREATE_NEW_CONSOLE)
    Close()


def Close():
    ImageUI.Exit()
    settings.Set("UI", "X", variables.WindowX)
    settings.Set("UI", "Y", variables.WindowY)
    settings.Set("UI", "Width", variables.WindowWidth)
    settings.Set("UI", "Height", variables.WindowHeight)
    console.RestoreConsole()
    console.CloseConsole()
    variables.Break = True


def Update():
    if SimpleWindow.GetMinimized(variables.Name):
        SimpleWindow.Show(variables.Name, variables.Frame)
        return

    if SimpleWindow.GetOpen(variables.Name) != True:
        Close()
        return

    WindowX, WindowY = SimpleWindow.GetPosition(variables.Name)
    WindowWidth, WindowHeight = SimpleWindow.GetSize(variables.Name)
    if (WindowX, WindowY, WindowWidth, WindowHeight) != (variables.WindowX, variables.WindowY, variables.WindowWidth, variables.WindowHeight):
        Resize(WindowX, WindowY, WindowWidth, WindowHeight)

    Left = 0
    Top = 0
    Right = WindowWidth - 1
    Bottom = WindowHeight - 1


    global ShowContextMenu
    if ImageUI.States.RightClicked:
        ShowContextMenu = True
    if ImageUI.States.LeftClicked:
        ShowContextMenu = False

    if ShowContextMenu:
        ImageUI.Button("Restart",
                       X1=ImageUI.States.RightClickPosition[0],
                       Y1=ImageUI.States.RightClickPosition[1],
                       X2=ImageUI.States.RightClickPosition[0] + 200,
                       Y2=ImageUI.States.RightClickPosition[1] + 30,
                       ID="ContextMenuRestart",
                       Layer=1,
                       OnPress=lambda: Restart())

        ImageUI.Button("Close",
                       X1=ImageUI.States.RightClickPosition[0],
                       Y1=ImageUI.States.RightClickPosition[1] + 35,
                       X2=ImageUI.States.RightClickPosition[0] + 200,
                       Y2=ImageUI.States.RightClickPosition[1] + 65,
                       ID="ContextMenuClose",
                       Layer=1,
                       OnPress=lambda: Close())

        ImageUI.Button("Search for updates",
                       X1=ImageUI.States.RightClickPosition[0],
                       Y1=ImageUI.States.RightClickPosition[1] + 70,
                       X2=ImageUI.States.RightClickPosition[0] + 200,
                       Y2=ImageUI.States.RightClickPosition[1] + 100,
                       ID="ContextMenuUpdate",
                       Layer=1,
                       OnPress=lambda: updater.CheckForUpdates())

    Tabs = ["Menu", "Plugins", "Settings"]
    for i, Tab in enumerate(Tabs):
        ImageUI.Button(Text=Tab,
                       X1=Left + i / len(Tabs) * Right + 5,
                       Y1=Top + 5,
                       X2=Left + (i + 1)  / len(Tabs) * Right - 5,
                       Y2=Top + 44,
                       ID=f"TabButton{Tab}",
                       OnPress=lambda Tab = Tab: {setattr(variables, "Page", Tab), settings.Set("UI", "Page", Tab)},
                       Color=((28, 28, 28) if variables.Theme == "Dark" else (250, 250, 250)) if Tab == variables.Page else ((47, 47, 47) if variables.Theme == "Dark" else (231, 231, 231)),
                       HoverColor=((28, 28, 28) if variables.Theme == "Dark" else (250, 250, 250)) if Tab == variables.Page else ((41, 41, 41) if variables.Theme == "Dark" else (244, 244, 244)))

    if variables.Page == "Update":
        ImageUI.Label(Text=f"Update Available:\n{variables.Version} -> {variables.RemoteVersion}",
                      X1=Left,
                      Y1=Top + 50,
                      X2=Right,
                      Y2=Top + 100,
                      ID="UpdateAvailable")

        ImageUI.Label(Text=f"Changelog:\n\n{variables.Changelog}",
                      X1=Left,
                      Y1=Top + 100,
                      X2=Right,
                      Y2=Bottom - 50,
                      ID="Changelog")

        ImageUI.Button(Text="Update",
                       X1=Left + 10,
                       Y1=Bottom - 50,
                       X2=Right / 2 - 5,
                       Y2=Bottom - 10,
                       ID="UpdateButton",
                       OnPress=lambda: updater.Update())

        ImageUI.Button(Text="Don't Update",
                       X1=Right / 2 + 5,
                       Y1=Bottom - 50,
                       X2=Right - 10,
                       Y2=Bottom - 10,
                       ID="Don'tUpdateButton",
                       OnPress=lambda: setattr(variables, "Page", "Menu"))

    if variables.Page == "CrashReport":
        ImageUI.Label(Text="Crash Reporter",
                      X1=Left,
                      Y1=Top + 60,
                      X2=Right,
                      Y2=Top + 100,
                      ID="CrashReportTitle")

        ImageUI.Label(Text="Do you want the app to send anonymous crash reports to the developers?\nNo personal information is sent and all paths have the username censored.\nWe take all crash reports seriously and will try to fix the issue as soon as possible.\nDo you want to enable the crash reporting?",
                      X1=Left,
                      Y1=Top + 110,
                      X2=Right,
                      Y2=Bottom - 60,
                      ID="CrashReportQuestion")

        ImageUI.Button(Text="Yes",
                       X1=Left + 10,
                       Y1=Bottom - 50,
                       X2=Right / 2 - 5,
                       Y2=Bottom - 10,
                       ID="CrashReportButtonYes",
                       OnPress=lambda: {setattr(variables, "Page", "Menu"), setattr(server, "AllowCrashReports", True), settings.Set("CrashReports", "SendCrashReports", True)})

        ImageUI.Button(Text="No",
                       X1=Right / 2 + 5,
                       Y1=Bottom - 50,
                       X2=Right - 10,
                       Y2=Bottom - 10,
                       ID="CrashReportButtonNo",
                       OnPress=lambda: {setattr(variables, "Page", "Menu"), setattr(server, "AllowCrashReports", False), settings.Set("CrashReports", "SendCrashReports", False)})

    if variables.Page == "CUDA":
        if variables.CUDAInstalled != "Loading..." and variables.CUDAAvailable != "Loading..." and variables.CUDACompatible != "Loading..." and variables.CUDADetails != "Loading...":
            if variables.CUDAInstalled == False and variables.CUDAAvailable == False and variables.CUDACompatible == False:
                Message = "CUDA is not installed, not available and not compatible."
            elif variables.CUDAInstalled == True and variables.CUDAAvailable == False and variables.CUDACompatible == False:
                Message = "CUDA is installed but not available and not compatible."
            elif variables.CUDAInstalled == True and variables.CUDAAvailable == False and variables.CUDACompatible == True:
                Message = "CUDA is installed but not available, probably\nbecause your NVIDIA GPU is not compatible."
            elif variables.CUDAInstalled == False and variables.CUDAAvailable == False and variables.CUDACompatible == True:
                Message = "CUDA is not installed and not available, but it is compatible."
            elif variables.CUDAInstalled == False and variables.CUDAAvailable == True and variables.CUDACompatible == True:
                Message = "CUDA is not installed but available and compatible,\nprobably because Python is using a CUDA installation\noutside of the app environment."
            elif variables.CUDAInstalled == True and variables.CUDAAvailable == True and variables.CUDACompatible == True:
                Message = "CUDA is installed, available and compatible."
            else:
                Message = f"INSTALLED: {variables.CUDAInstalled} AVAILABLE: {variables.CUDAAvailable} COMPATIBLE: {variables.CUDACompatible}"
            ImageUI.Label(Text="When CUDA is installed and available, the app will run AI models\non your NVIDIA GPU which will result in a significant speed increase.",
                          X1=Left + 10,
                          Y1=Top + 60,
                          X2=Right - 10,
                          Y2=Top + 110,
                          ID="CUDATitle")

            ImageUI.Label(Text=f"{Message}",
                          X1=Left + 10,
                          Y1=Top + 110,
                          X2=Right - 10,
                          Y2=Top + 160,
                          ID="CUDAInfo")

            ImageUI.Label(Text=f"Details:\n{variables.CUDADetails}",
                          X1=Left + 10,
                          Y1=Top + 160,
                          X2=Right - 10,
                          Y2=Top + 280,
                          ID="CUDADetails")

            ImageUI.Label(Text="WARNING:\nThis app is using embedded Python which causes problems with Torch + CUDA!\nBecause of this, installing CUDA probably won't work or break the app!",
                          X1=Left + 10,
                          Y1=Top + 280,
                          X2=Right - 10,
                          Y2=Top + 320,
                          ID="CUDAWarning",
                          TextColor=(0, 0, 255))

            if variables.CUDAInstalled == False and variables.CUDACompatible == True:
                ImageUI.Button(Text="Install CUDA libraries (3GB)",
                               X1=Right / 2 + 5,
                               Y1=Bottom - 50,
                               X2=Right - 10,
                               Y2=Bottom - 10,
                               ID="InstallCUDAButton",
                               OnPress=lambda: {setattr(variables, "Page", "Menu"), pytorch.InstallCUDA()})

                ImageUI.Button(Text="Keep running on CPU",
                               X1=Left + 10,
                               Y1=Bottom - 50,
                               X2=Right / 2 - 5,
                               Y2=Bottom - 10,
                               ID="Don'tInstallCUDAButton",
                               OnPress=lambda: {setattr(variables, "Page", "Menu")})
            elif variables.CUDAInstalled == False and variables.CUDAAvailable == False and variables.CUDACompatible == False:
                ImageUI.Button(Text="Install CUDA libraries anyway (3GB)",
                               X1=Right / 2 + 5,
                               Y1=Bottom - 50,
                               X2=Right - 10,
                               Y2=Bottom - 10,
                               ID="InstallCUDAButton",
                               OnPress=lambda: {setattr(variables, "Page", "Menu"), pytorch.InstallCUDA()})

                ImageUI.Button(Text="Keep running on CPU",
                               X1=Left + 10,
                               Y1=Bottom - 50,
                               X2=Right / 2  - 5,
                               Y2=Bottom - 10,
                               ID="Don'tInstallCUDAButton",
                               OnPress=lambda: {setattr(variables, "Page", "Menu")})
            elif variables.CUDAInstalled == True and variables.CUDAAvailable == True and variables.CUDACompatible == True:
                ImageUI.Button(Text="Uninstall CUDA libraries",
                               X1=Right / 2 + 5,
                               Y1=Bottom - 50,
                               X2=Right - 10,
                               Y2=Bottom - 10,
                               ID="UninstallCUDAButton",
                               OnPress=lambda: {setattr(variables, "Page", "Menu"), pytorch.UninstallCUDA()})

                ImageUI.Button(Text="Keep running on GPU with CUDA",
                               X1=Left + 10,
                               Y1=Bottom - 50,
                               X2=Right / 2 - 5,
                               Y2=Bottom - 10,
                               ID="Don'tUninstallCUDAButton",
                               OnPress=lambda: {setattr(variables, "Page", "Menu")})
            else:
                ImageUI.Button(Text="Uninstall CUDA libraries",
                               X1=Right / 2 + 5,
                               Y1=Bottom - 50,
                               X2=Right - 10,
                               Y2=Bottom - 10,
                               ID="UninstallCUDAButton",
                               OnPress=lambda: {setattr(variables, "Page", "Menu"), pytorch.UninstallCUDA()})

                ImageUI.Button(Text="Keep running on CPU with CUDA",
                               X1=Left + 10,
                               Y1=Bottom - 50,
                               X2=Right / 2 - 5,
                               Y2=Bottom - 10,
                               ID="Don'tUninstallCUDAButton",
                               OnPress=lambda: {setattr(variables, "Page", "Menu")})
        else:
            ImageUI.Label(Text=f"Checking your CUDA compatibility, please wait...",
                          X1=Left + 10,
                          Y1=Top + 10,
                          X2=Right - 10,
                          Y2=Bottom - 10,
                          ID="CheckingCUDA")

    if variables.Page == "Menu":
        ImageUI.Label(Text=f"ETS2LA-Lite v{variables.Version}",
                      X1=Left,
                      Y1=Top + 50,
                      X2=Right,
                      Y2=Top + 95,
                      ID="MenuTitle",
                      FontSize=17)

        ImageUI.Label(Text=f"Users online: {variables.UserCount}",
                      X1=Left,
                      Y1=Bottom - 45,
                      X2=Right,
                      Y2=Bottom - 5,
                      ID="MenuStatus",
                      TextColor=(128, 128, 128))

        ImageUI.Button(Text="Open ETS2LA Website",
                       X1=Right * 0.25,
                       Y1=Bottom / 2 - 70,
                       X2=Right * 0.75,
                       Y2=Bottom / 2 - 30,
                       ID="MenuWebsite",
                       OnPress=lambda: webbrowser.open("https://ets2la.com"))

        ImageUI.Button(Text="Open GitHub Website",
                       X1=Right * 0.25,
                       Y1=Bottom / 2 - 20,
                       X2=Right * 0.75,
                       Y2=Bottom / 2 + 20,
                       ID="MenuGitHub",
                       OnPress=lambda: webbrowser.open("https://github.com/ETS2LA"))

        ImageUI.Button(Text="Open ETS2LA Discord",
                       X1=Right * 0.25,
                       Y1=Bottom / 2 + 30,
                       X2=Right * 0.75,
                       Y2=Bottom / 2 + 70,
                       ID="MenuDiscord",
                       OnPress=lambda: webbrowser.open("https://ets2la.com/discord"))

    if variables.Page == "Plugins":
        for i, Plugin in enumerate(variables.AvailablePlugins):
            ImageUI.Switch(Text=Plugin,
                           X1=Left + 10,
                           Y1=Top + 55 + 30 * i,
                           X2=Right - 10,
                           Y2=Top + 85 + 30 * i,
                           ID=f"{Plugin}Switch",
                           State=EnabledPlugins[Plugin],
                           OnChange=lambda State, Plugin=Plugin: {settings.Set("Plugins", Plugin, State), plugins.ManagePlugins(Plugin=Plugin, Action="Start" if State else "Stop")})

    if variables.Page == "Settings":
        ImageUI.Dropdown(Title="Language",
                         Items=AvailableLanguages,
                         DefaultItem=variables.Language,
                         X1=Left + 10,
                         Y1=Top + 60,
                         X2=Right / 2 - 5,
                         Y2=Top + 95,
                         ID="LanguageDropdown",
                         OnChange=lambda Item: {settings.Set("UI", "Language", Item), setattr(variables, "Language", Item), ImageUI.Translations.SetTranslator(SourceLanguage="English", DestinationLanguage=Item)})

        ImageUI.Dropdown(Title="Theme",
                         Items=["Dark", "Light"],
                         DefaultItem=variables.Theme,
                         X1=Right / 2 + 5,
                         Y1=Top + 60,
                         X2=Right -10,
                         Y2=Top + 95,
                         ID="ThemeDropdown",
                         OnChange=SetTheme)

        ImageUI.Button(Text="Check CUDA (GPU) Support",
                       X1=Left + 10,
                       Y1=Top + 105,
                       X2=Right / 2 - 5,
                       Y2=Top + 140,
                       ID="CheckCUDAButton",
                       OnPress=lambda: {setattr(variables, "Page", "CUDA"), pytorch.CheckCUDA()})

        ImageUI.Button(Text="Game Paths",
                       X1=Right / 2 + 5,
                       Y1=Top + 105,
                       X2=Right - 10,
                       Y2=Top + 140,
                       ID="GamePathsButton",
                       OnPress=lambda: setattr(variables, "Page", "GamePathInput"))

        ImageUI.Switch(Text="Hide Console",
                       X1=Left + 10,
                       Y1=Top + 150,
                       X2=Right / 2 - 5,
                       Y2=Top + 175,
                       ID="HideConsoleSwitch",
                       State=HideConsoleSwitch,
                       OnChange=lambda State: {settings.Set("Console", "HideConsole", State), console.HideConsole() if State else console.RestoreConsole()})

        ImageUI.Switch(Text="Send Anonymous Crash Reports",
                       X1=Left + 10,
                       Y1=Top + 180,
                       X2=Right / 2 - 5,
                       Y2=Top + 205,
                       ID="SendAnonymousCrashReportsSwitch",
                       State=SendCrashReportsSwitch,
                       OnChange=lambda State: {settings.Set("CrashReports", "SendCrashReports", State), setattr(server, "AllowCrashReports", State), threading.Thread(target=server.GetUserCount, daemon=True).start()})

        ImageUI.Label(Text=f"Enable/Disable Key:",
                       X1=Left + 10,
                       Y1=Top + 210,
                       X2=Right / 2 - 5,
                       Y2=Top + 235,
                       ID="EnableDisableKeyLabel",
                       Align="Left",
                       AlignPadding=0)

        ImageUI.Input(X1=Left + 10,
                      Y1=Top + 235,
                      X2=Right / 4,
                      Y2=Top + 265,
                      ID="EnableDisableKeyInput",
                      DefaultInput=EnableDisableKey,
                      Placeholder="Default: n",
                      OnChange=EnableDisableKeyCallback)

    if variables.Page == "GamePathInput":
        ImageUI.Label(Text="Set the paths to the games here.\nNormally they are found automatically.",
                      X1=Left,
                      Y1=Top + 50,
                      X2=Right,
                      Y2=Top + 110,
                      ID="GamePathTitle")

        ImageUI.Label(Text="Euro Truck Simulator 2 Path:",
                      X1=Right * 0.1,
                      Y1=Bottom / 2 - 70,
                      X2=Right * 0.9,
                      Y2=Bottom / 2 - 45,
                      ID="ETS2PathTitle",
                      Align="Left",
                      AlignPadding=0)

        ImageUI.Input(X1=Right * 0.1,
                      Y1=Bottom / 2 - 45,
                      X2=Right * 0.9,
                      Y2=Bottom / 2 - 10,
                      ID="ETS2PathInput",
                      DefaultInput=variables.ETS2Path,
                      Placeholder="Path to the 'Euro Truck Simulator 2' folder. Leave empty if not installed!",
                      OnChange=lambda Input: {settings.Set("Setup", "ETS2Path", Input)})

        ImageUI.Label(Text="American Truck Simulator Path:",
                      X1=Right * 0.1,
                      Y1=Bottom / 2 + 10,
                      X2=Right * 0.9,
                      Y2=Bottom / 2 + 35,
                      ID="ATSPathTitle",
                      Align="Left",
                      AlignPadding=0)

        ImageUI.Input(X1=Right * 0.1,
                      Y1=Bottom / 2 + 35,
                      X2=Right * 0.9,
                      Y2=Bottom / 2 + 70,
                      ID="ATSPathInput",
                      DefaultInput=variables.ATSPath,
                      Placeholder="Path to the 'American Truck Simulator' folder. Leave empty if not installed!",
                      OnChange=lambda Input: {settings.Set("Setup", "ATSPath", Input)})

        ImageUI.Button(Text="Ok",
                       X1=Left + 10,
                       Y1=Bottom - 50,
                       X2=Right - 10,
                       Y2=Bottom - 10,
                       ID="GamePathOkButton",
                       OnPress=lambda: {setup.CopyDLLs(), setattr(variables, "Page", "Menu")})

    Frame = variables.Background.copy()
    variables.Frame = ImageUI.Update(WindowHWND=SimpleWindow.GetHandle(variables.Name), Frame=Frame)
    SimpleWindow.Show(variables.Name, Frame=variables.Frame)