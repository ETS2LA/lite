import src.variables as variables
import src.settings as settings
import src.ui as ui

import requests
import time
import os

def CheckForUpdates():
    if float(settings.Get("Updater", "LastRemoteCheck", 0)) + 600 < time.time():
        remote_version = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/version.txt").text.strip()
        changelog = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/changelog.txt").text.strip()
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

def Update():
    try:
        os.chdir(variables.PATH)
        os.system("git stash")
        os.system("git pull")
    except Exception as e:
        print("Failed to update: " + str(e))