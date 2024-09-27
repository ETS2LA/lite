import src.variables as variables
import src.settings as settings
import src.plugins as plugins
import src.ui as ui

import requests
import time
import os

def CheckForUpdates():
    if variables.DEVMODE:
        variables.POPUP = ["Ignoring update check because of development mode.", 0, 0.65]
        return
    if settings.Get("Updater", "LastRemoteCheck", 0) + 600 < time.time():
        try:
            remote_version = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/config/version.txt").text.strip()
            changelog = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/config/changelog.txt").text.strip()
        except:
            remote_version = "404: Not Found"
            changelog = "404: Not Found"
        if remote_version != "404: Not Found" and changelog != "404: Not Found":
            settings.Set("Updater", "LastRemoteCheck", time.time())
            settings.Set("Updater", "RemoteVersion", remote_version)
            settings.Set("Updater", "Changelog", changelog)
    else:
        remote_version = settings.Get("Updater", "RemoteVersion")
        changelog = settings.Get("Updater", "Changelog")
    variables.REMOTE_VERSION = remote_version
    variables.CHANGELOG = changelog
    if remote_version != variables.VERSION:
        variables.PAGE = "Update"
        ui.SetTitleBarHeight(0)
    else:
        variables.POPUP = ["No updates available.", 0, 0.5]

def Update():
    if variables.DEVMODE:
        variables.POPUP = ["Ignoring update request because of development mode.", 0, 0.65]
        ui.SetTitleBarHeight(50)
        variables.PAGE = "Menu"
        return
    plugins.ManagePlugins(Plugin="All", Action="Stop")
    try:
        os.chdir(variables.PATH)
        os.system("git stash >nul 2>&1")
        os.system("git pull >nul 2>&1")
    except:
        pass
    ui.Restart()