import src.variables as variables
import src.settings as settings
import src.console as console
import src.plugins as plugins
import src.pytorch as pytorch
import src.updater as updater
import src.server as server

from ctypes import windll, byref, sizeof, c_int
import SimpleWindow
import numpy as np
import subprocess
import webbrowser
import threading
import win32con
import win32gui
import ImageUI
import ctypes
import mouse
import math
import time
import cv2


AvailableLanguages = list(ImageUI.Translations.GetAvailableLanguages().keys())
EnabledPlugins = {Plugin: settings.Get("Plugins", Plugin, False) for Plugin in variables.AvailablePlugins}
ShowContextMenu = False


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
                            Resizable=True,
                            TopMost=False,
                            Undestroyable=False,
                            Icon=f"{variables.Path}app/assets/favicon.ico")

    SimpleWindow.Show(variables.Name, variables.Background)

    ImageUI.Translations.SetTranslator(SourceLanguage="English", DestinationLanguage=variables.Language)
    Update()


def Resize(WindowWidth, WindowHeight):
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
        variables.WindowX, variables.WindowY, variables.WindowWidth, variables.WindowHeight = WindowX, WindowY, WindowWidth, WindowHeight
        Resize(WindowWidth, WindowHeight)

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
                       Layer=1,
                       OnPress=lambda: Restart())

        ImageUI.Button("Close",
                       X1=ImageUI.States.RightClickPosition[0],
                       Y1=ImageUI.States.RightClickPosition[1] + 35,
                       X2=ImageUI.States.RightClickPosition[0] + 200,
                       Y2=ImageUI.States.RightClickPosition[1] + 65,
                       Layer=1,
                       OnPress=lambda: Close())

        ImageUI.Button("Search for updates",
                       X1=ImageUI.States.RightClickPosition[0],
                       Y1=ImageUI.States.RightClickPosition[1] + 70,
                       X2=ImageUI.States.RightClickPosition[0] + 200,
                       Y2=ImageUI.States.RightClickPosition[1] + 100,
                       Layer=1,
                       OnPress=lambda: updater.CheckForUpdates())

    Tabs = ["Menu", "Plugins", "Settings"]
    for i, Tab in enumerate(Tabs):
        ImageUI.Button(Text=Tab,
                       X1=Top + i / len(Tabs) * Right + 5,
                       Y1=Left + 5,
                       X2=Top + (i + 1)  / len(Tabs) * Right - 5,
                       Y2=Top + 44,
                       OnPress=lambda Tab = Tab: {setattr(variables, "Page", Tab), settings.Set("UI", "Page", Tab)},
                       Color=variables.TabButtonSelectedColor if Tab == variables.Page else variables.TabButtonColor,
                       HoverColor=variables.TabButtonSelectedHoverColor if Tab == variables.Page else variables.TabButtonHoverColor)

    if variables.Page == "Update":
        ImageUI.Label(Text=f"Update Available:\n{variables.Version} -> {variables.RemoteVersion}",
                      X1=Top,
                      Y1=Left + 60,
                      X2=Right,
                      Y2=Top + 100)

        ImageUI.Label(Text=f"Changelog:\n\n{variables.Changelog}",
                      X1=Left,
                      Y1=Top + 110,
                      X2=Right,
                      Y2=Bottom - 60)

        ImageUI.Button(Text="Update",
                       X1=Left + 10,
                       Y1=Bottom - 50,
                       X2=Right / 2 - 5,
                       Y2=Bottom - 10,
                       OnPress=lambda: updater.Update())

        ImageUI.Button(Text="Don't Update",
                       X1=Right / 2 + 5,
                       Y1=Bottom - 50,
                       X2=Right - 10,
                       Y2=Bottom - 10,
                       OnPress=lambda: setattr(variables, "Page", "Menu"))

    if variables.Page == "CrashReport":
        ImageUI.Label(Text="Crash Reporter",
                      X1=Left,
                      Y1=Top + 60,
                      X2=Right,
                      Y2=Top + 100)

        ImageUI.Label(Text="Do you want the app to send anonymous crash reports to the developers?\nNo personal information is sent and all paths have the username censored.\nWe take all crash reports seriously and will try to fix the issue as soon as possible.\nDo you want to enable the crash reporting?",
                      X1=Left,
                      Y1=Top + 110,
                      X2=Right,
                      Y2=Bottom - 60)

        ImageUI.Button(Text="Yes",
                       X1=Left + 10,
                       Y1=Bottom - 50,
                       X2=Right / 2 - 5,
                       Y2=Bottom - 10,
                       OnPress=lambda: {setattr(variables, "Page", "Menu"), setattr(server, "AllowCrashReports", True), settings.Set("CrashReports", "SendCrashReports", True)})

        ImageUI.Button(Text="No",
                       X1=Right / 2 + 5,
                       Y1=Bottom - 50,
                       X2=Right - 10,
                       Y2=Bottom - 10,
                       OnPress=lambda: {setattr(variables, "Page", "Menu"), setattr(server, "AllowCrashReports", False), settings.Set("CrashReports", "SendCrashReports", False)})

    #if variables.PAGE == "CUDA":
    #    if variables.CUDA_INSTALLED != "Loading..." and variables.CUDA_AVAILABLE != "Loading..." and variables.CUDA_COMPATIBLE != "Loading..." and variables.CUDA_DETAILS != "Loading...":
    #        if variables.CUDA_INSTALLED == False and variables.CUDA_AVAILABLE == False and variables.CUDA_COMPATIBLE == False:
    #            Message = "CUDA is not installed, not available and not compatible."
    #        elif variables.CUDA_INSTALLED == True and variables.CUDA_AVAILABLE == False and variables.CUDA_COMPATIBLE == False:
    #            Message = "CUDA is installed but not available and not compatible."
    #        elif variables.CUDA_INSTALLED == True and variables.CUDA_AVAILABLE == False and variables.CUDA_COMPATIBLE == True:
    #            Message = "CUDA is installed but not available, probably\nbecause your NVIDIA GPU is not compatible."
    #        elif variables.CUDA_INSTALLED == False and variables.CUDA_AVAILABLE == False and variables.CUDA_COMPATIBLE == True:
    #            Message = "CUDA is not installed and not available, but it is compatible."
    #        elif variables.CUDA_INSTALLED == False and variables.CUDA_AVAILABLE == True and variables.CUDA_COMPATIBLE == True:
    #            Message = "CUDA is not installed but available and compatible,\nprobably because Python is using a CUDA installation\noutside of the app environment."
    #        elif variables.CUDA_INSTALLED == True and variables.CUDA_AVAILABLE == True and variables.CUDA_COMPATIBLE == True:
    #            Message = "CUDA is installed, available and compatible."
    #        else:
    #            Message = f"INSTALLED: {variables.CUDA_INSTALLED} AVAILABLE: {variables.CUDA_AVAILABLE} COMPATIBLE: {variables.CUDA_COMPATIBLE}"
    #        variables.ITEMS.append({
    #            "Type": "Label",
    #            "Text": "When CUDA is installed and available, the app will run AI models\non your NVIDIA GPU which will result in a significant speed increase.",
    #            "X1": 10,
    #            "Y1": 10,
    #            "X2": variables.CANVAS_RIGHT - 10,
    #            "Y2": 60})
#
    #        variables.ITEMS.append({
    #            "Type": "Label",
    #            "Text": f"{Message}",
    #            "X1": 10,
    #            "Y1": 80,
    #            "X2": variables.CANVAS_RIGHT - 10,
    #            "Y2": 130})
#
    #        variables.ITEMS.append({
    #            "Type": "Label",
    #            "Text": f"Details:\n{variables.CUDA_DETAILS}",
    #            "X1": 10,
    #            "Y1": 150,
    #            "X2": variables.CANVAS_RIGHT - 10,
    #            "Y2": 275})
#
    #        if variables.CUDA_INSTALLED == False and variables.CUDA_COMPATIBLE == True:
    #            variables.ITEMS.append({
    #                "Type": "Button",
    #                "Text": "Install CUDA libraries (3GB)",
    #                "Function": lambda: {setattr(variables, "PAGE", "Canvas"), pytorch.InstallCUDA()},
    #                "X1": variables.CANVAS_RIGHT / 2 + 5,
    #                "Y1": variables.CANVAS_BOTTOM - 60,
    #                "X2": variables.CANVAS_RIGHT - 10,
    #                "Y2": variables.CANVAS_BOTTOM - 10})
#
    #            variables.ITEMS.append({
    #                "Type": "Button",
    #                "Text": "Keep running on CPU",
    #                "Function": lambda: {setattr(variables, "PAGE", "Canvas")},
    #                "X1": 10,
    #                "Y1": variables.CANVAS_BOTTOM - 60,
    #                "X2": variables.CANVAS_RIGHT / 2 - 5,
    #                "Y2": variables.CANVAS_BOTTOM - 10})
    #        elif variables.CUDA_INSTALLED == False and variables.CUDA_AVAILABLE == False and variables.CUDA_COMPATIBLE == False:
    #            variables.ITEMS.append({
    #                "Type": "Button",
    #                "Text": "Install CUDA libraries anyway (3GB)",
    #                "Function": lambda: {setattr(variables, "PAGE", "Canvas"), pytorch.InstallCUDA()},
    #                "X1": variables.CANVAS_RIGHT / 2 + 5,
    #                "Y1": variables.CANVAS_BOTTOM - 60,
    #                "X2": variables.CANVAS_RIGHT - 10,
    #                "Y2": variables.CANVAS_BOTTOM - 10})
#
    #            variables.ITEMS.append({
    #                "Type": "Button",
    #                "Text": "Keep running on CPU",
    #                "Function": lambda: {setattr(variables, "PAGE", "Canvas")},
    #                "X1": 10,
    #                "Y1": variables.CANVAS_BOTTOM - 60,
    #                "X2": variables.CANVAS_RIGHT / 2 - 5,
    #                "Y2": variables.CANVAS_BOTTOM - 10})
    #        elif variables.CUDA_INSTALLED == True and variables.CUDA_AVAILABLE == True and variables.CUDA_COMPATIBLE == True:
    #            variables.ITEMS.append({
    #                "Type": "Button",
    #                "Text": "Uninstall CUDA libraries",
    #                "Function": lambda: {setattr(variables, "PAGE", "Canvas"), pytorch.UninstallCUDA()},
    #                "X1": variables.CANVAS_RIGHT / 2 + 5,
    #                "Y1": variables.CANVAS_BOTTOM - 60,
    #                "X2": variables.CANVAS_RIGHT - 10,
    #                "Y2": variables.CANVAS_BOTTOM - 10})
#
    #            variables.ITEMS.append({
    #                "Type": "Button",
    #                "Text": "Keep running on GPU with CUDA",
    #                "Function": lambda: {setattr(variables, "PAGE", "Canvas")},
    #                "X1": 10,
    #                "Y1": variables.CANVAS_BOTTOM - 60,
    #                "X2": variables.CANVAS_RIGHT / 2 - 5,
    #                "Y2": variables.CANVAS_BOTTOM - 10})
    #        else:
    #            variables.ITEMS.append({
    #                "Type": "Button",
    #                "Text": "Uninstall CUDA libraries",
    #                "Function": lambda: {setattr(variables, "PAGE", "Canvas"), pytorch.UninstallCUDA()},
    #                "X1": variables.CANVAS_RIGHT / 2 + 5,
    #                "Y1": variables.CANVAS_BOTTOM - 60,
    #                "X2": variables.CANVAS_RIGHT - 10,
    #                "Y2": variables.CANVAS_BOTTOM - 10})
#
    #            variables.ITEMS.append({
    #                "Type": "Button",
    #                "Text": "Keep running on CPU with CUDA",
    #                "Function": lambda: {setattr(variables, "PAGE", "Canvas")},
    #                "X1": 10,
    #                "Y1": variables.CANVAS_BOTTOM - 60,
    #                "X2": variables.CANVAS_RIGHT / 2 - 5,
    #                "Y2": variables.CANVAS_BOTTOM - 10})
    #    else:
    #        variables.RENDER_FRAME = True
    #        variables.ITEMS.append({
    #            "Type": "Label",
    #            "Text": f"Checking your CUDA compatibility, please wait...",
    #            "X1": 10,
    #            "Y1": 10,
    #            "X2": variables.CANVAS_RIGHT - 10,
    #            "Y2": variables.CANVAS_BOTTOM - 10})

    if variables.Page == "Menu":
        ImageUI.Label(Text=f"ETS2LA-Lite v{variables.Version}",
                      X1=Left,
                      Y1=Top + 50,
                      X2=Right,
                      Y2=Top + 95,
                      FontSize=17)

        ImageUI.Label(Text=f"Users online: {variables.UserCount}",
                      X1=Left,
                      Y1=Bottom - 45,
                      X2=Right,
                      Y2=Bottom - 5,
                      TextColor=(128, 128, 128))

        ImageUI.Button(Text="Open ETS2LA Website",
                       X1=Right * 0.25,
                       Y1=Bottom / 2 - 70,
                       X2=Right * 0.75,
                       Y2=Bottom / 2 - 30,
                       OnPress=lambda: webbrowser.open("https://ets2la.com"))

        ImageUI.Button(Text="Open GitHub Website",
                       X1=Right * 0.25,
                       Y1=Bottom / 2 - 20,
                       X2=Right * 0.75,
                       Y2=Bottom / 2 + 20,
                       OnPress=lambda: webbrowser.open("https://github.com/ETS2LA"))

        ImageUI.Button(Text="Open ETS2LA Discord",
                       X1=Right * 0.25,
                       Y1=Bottom / 2 + 30,
                       X2=Right * 0.75,
                       Y2=Bottom / 2 + 70,
                       OnPress=lambda: webbrowser.open("https://ets2la.com/discord"))

    if variables.Page == "Plugins":
        for i, Plugin in enumerate(variables.AvailablePlugins):
            ImageUI.Switch(Text=Plugin,
                           X1=Left + 10,
                           Y1=Top + 55 + 30 * i,
                           X2=Top + Right,
                           Y2=Top + 85 + 30 * i,
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
                         OnChange=lambda Item: {settings.Set("UI", "Language", Item), setattr(variables, "Language", Item), ImageUI.Translations.SetTranslator(SourceLanguage="English", DestinationLanguage=Item)})

        ImageUI.Dropdown(Title="Theme",
                         Items=["Dark", "Light"],
                         DefaultItem=variables.Theme,
                         X1=Right / 2 + 5,
                         Y1=Top + 60,
                         X2=Right -10,
                         Y2=Top + 95,
                         OnChange=lambda Item: {settings.Set("UI", "Theme", Item), Restart() if variables.Theme != Item else None})

        ImageUI.Button(Text="Check CUDA (GPU) Support",
                       X1=Left + 10,
                       Y1=Top + 105,
                       X2=Right / 2 - 5,
                       Y2=Top + 140,
                       OnPress=lambda: setattr(variables, "Page", "CUDA"))

        ImageUI.Switch(Text="Hide Console",
                       X1=Left + 10,
                       Y1=Top + 150,
                       X2=Right,
                       Y2=Top + 175,
                       OnChange=lambda State: {settings.Set("Console", "HideConsole", State), console.HideConsole() if State else console.RestoreConsole()})

        ImageUI.Switch(Text="Send Anonymous Crash Reports",
                       X1=Left + 10,
                       Y1=Top + 180,
                       X2=Right,
                       Y2=Top + 205,
                       OnChange=lambda State: {settings.Set("CrashReports", "SendCrashReports", State), setattr(server, "AllowCrashReports", State), threading.Thread(target=server.GetUserCount, daemon=True).start()})

    Frame = variables.Background.copy()
    variables.Frame = ImageUI.Update(WindowHWND=SimpleWindow.GetHandle(variables.Name), Frame=Frame)
    SimpleWindow.Show(variables.Name, Frame=variables.Frame)