import src.variables as variables
import src.settings as settings
import src.console as console
import src.ui as ui

import threading
import requests
import time
import os


if settings.Get("Console", "HideConsole", False):
    console.HideConsole()


remote_version = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/version.txt").text.strip()
changelog = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/changelog.txt").text.strip()
if remote_version == variables.VERSION:
    print("An update is available: " + remote_version)
    print(f"Changelog:\n{changelog}")
    if helpers.AskOkCancel("Updater", f"We have detected an update, do you want to install it?\nCurrent - {'.'.join(currentVer)}\nUpdated - {'.'.join(remoteVer)}\n\nChangelog:\n{changelog}"):
        os.chdir(variables.PATH)
        os.system("git stash")
        os.system("git pull")
else:
    print("No update available, current version: " + variables.VERSION)

ui.initialize()
ui.createUI()


def run_thread():
    import plugins.NavigationDetectionAI.main as NavigationDetectionAI
    NavigationDetectionAI.Initialize()
    while variables.BREAK == False:
        NavigationDetectionAI.plugin()

#threading.Thread(target=run_thread, daemon=True).start()


while variables.BREAK == False:
    start = time.time()

    variables.ROOT.update()

    time_to_sleep = 1/60 - (time.time() - start)
    if time_to_sleep > 0:
        time.sleep(time_to_sleep)


if settings.Get("Console", "HideConsole", False):
    console.RestoreConsole()