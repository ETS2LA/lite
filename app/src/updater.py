import src.variables as variables
import src.settings as settings
import src.ui as ui

import requests
import time
import os

def CheckForUpdates(do_ui_update = True):
    if float(settings.Get("Updater", "LastRemoteCheck", "0")) + 600 < time.time():
        try:
            remote_version = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/config/version.txt").text.strip()
            changelog = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/config/changelog.txt").text.strip()
        except:
            remote_version = "404: Not Found"
            changelog = "404: Not Found"
        if remote_version != "404: Not Found" and changelog != "404: Not Found":
            settings.Set("Updater", "LastRemoteCheck", str(time.time()))
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
        if do_ui_update:
            ui.Update()
    else:
        variables.POPUP = ["No updates available.", 0, 0.5]

def Update():
    try:
        os.chdir(variables.PATH)
        os.system("git stash >nul 2>&1")
        os.system("git pull >nul 2>&1")
    except:
        pass
    ui.Restart()