import src.variables as variables
import src.settings as settings
import src.console as console
import src.helpers as helpers
import src.server as server
import src.ui as ui

import threading
import requests
import time
import os

if settings.Get("Console", "HideConsole", False):
    console.HideConsole()

ui.InitializeUI()

remote_version = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/version.txt").text.strip()
changelog = requests.get("https://raw.githubusercontent.com/ETS2LA/lite/main/changelog.txt").text.strip()
if remote_version != variables.VERSION or True:
    print("An update is available: " + remote_version)
    print(f"Changelog:\n{changelog}")

    variables.PAGE = "Update"

    while variables.BREAK == False:
        start = time.time()

        ui.HandleUI()

        time_to_sleep = 1/60 - (time.time() - start)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

else:
    print("No update available, current version: " + variables.VERSION)

helpers.RunEvery(60, lambda: server.Ping())
if settings.Get("CrashReports", "AllowCrashReports"):
    pass

import plugins.NavigationDetectionAI.main as NavigationDetectionAI
def run_thread():
    global FPS
    NavigationDetectionAI.Initialize()
    while variables.BREAK == False:
        FPS = NavigationDetectionAI.plugin()
threading.Thread(target=run_thread, daemon=True).start()

FPS = 0
FPS_UpdateTime = 0
MainMenu_UpdateTime = 0

while variables.BREAK == False:
    start = time.time()

    ui.HandleUI()

    time_to_sleep = 1/60 - (time.time() - start)
    if time_to_sleep > 0:
        time.sleep(time_to_sleep)

if settings.Get("Console", "HideConsole", False):
    console.RestoreConsole()
    console.CloseConsole()