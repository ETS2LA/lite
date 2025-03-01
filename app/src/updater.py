import src.variables as variables
import src.settings as settings
import src.plugins as plugins
import src.ui as ui

import subprocess
import requests
import ImageUI
import time

def CheckForUpdates():
    if variables.DevelopmentMode:
        Right = variables.WindowWidth - 1
        Bottom = variables.WindowHeight - 1
        ImageUI.Popup("Ignoring update check because of development mode.",
                      StartX1=Right * 0.25,
                      StartY1=Bottom,
                      StartX2=Right * 0.75,
                      StartY2=Bottom + 20,
                      EndX1=Right * 0.1,
                      EndY1=Bottom - 50,
                      EndX2=Right * 0.9,
                      EndY2=Bottom - 10)
        return
    if settings.Get("Updater", "LastRemoteCheck", 0) + 600 < time.time():
        try:
            RemoteVersion = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/config/version.txt").text.strip()
            Changelog = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/config/changelog.txt").text.strip()
        except:
            RemoteVersion = "404: Not Found"
            Changelog = "404: Not Found"
        if RemoteVersion != "404: Not Found" and Changelog != "404: Not Found":
            settings.Set("Updater", "LastRemoteCheck", time.time())
            settings.Set("Updater", "RemoteVersion", RemoteVersion)
            settings.Set("Updater", "Changelog", Changelog)
    else:
        RemoteVersion = settings.Get("Updater", "RemoteVersion")
        Changelog = settings.Get("Updater", "Changelog")
    variables.RemoteVersion = RemoteVersion
    variables.Changelog = Changelog
    if RemoteVersion != variables.Version:
        variables.Page = "Update"
    else:
        Right = variables.WindowWidth - 1
        Bottom = variables.WindowHeight - 1
        ImageUI.Popup("No updates available.",
                      StartX1=Right * 0.4,
                      StartY1=Bottom,
                      StartX2=Right * 0.6,
                      StartY2=Bottom + 20,
                      EndX1=Right * 0.25,
                      EndY1=Bottom - 50,
                      EndX2=Right * 0.75,
                      EndY2=Bottom - 10)


def Update():
    if variables.DevelopmentMode:
        Right = variables.WindowWidth - 1
        Bottom = variables.WindowHeight - 1
        ImageUI.Popup("Ignoring update request because of development mode.",
                      StartX1=Right * 0.25,
                      StartY1=Bottom,
                      StartX2=Right * 0.75,
                      StartY2=Bottom + 20,
                      EndX1=Right * 0.1,
                      EndY1=Bottom - 50,
                      EndX2=Right * 0.9,
                      EndY2=Bottom - 10)
        variables.Page = "Menu"
        return
    plugins.ManagePlugins(Plugin="All", Action="Stop")
    ui.Close()
    subprocess.Popen(f"{variables.Path}Update.bat", cwd=variables.Path, creationflags=subprocess.CREATE_NEW_CONSOLE)