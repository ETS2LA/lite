import src.variables as variables
import src.ui as ui

import requests
import os

def CheckForUpdates():
    remote_version = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/version.txt").text.strip()
    changelog = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/changelog.txt").text.strip()
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