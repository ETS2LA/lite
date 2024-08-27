import src.variables as variables
import src.settings as settings
import src.console as console
import src.helpers as helpers
import src.updater as updater
import src.server as server
import src.ui as ui

import threading
import time
import os

os.system("cls" if variables.OS == "nt" else "clear")
print("\nETS2LA-Lite\n-----------\n")

if settings.Get("Console", "HideConsole", False):
    console.HideConsole()

ui.Initialize()
updater.CheckForUpdates()
helpers.RunEvery(60, lambda: server.Ping())
server.variables.USERCOUNT = server.GetUserCount()

import plugins.NavigationDetectionAI.main as NavigationDetectionAI
def run_thread():
    global FPS
    NavigationDetectionAI.Initialize()
    while variables.BREAK == False:
        FPS = NavigationDetectionAI.plugin()
#threading.Thread(target=run_thread, daemon=True).start()

FPS = 0
FPS_UpdateTime = 0
MainMenu_UpdateTime = 0

while variables.BREAK == False:
    start = time.time()

    ui.Update()

    time_to_sleep = 1/60 - (time.time() - start)
    if time_to_sleep > 0:
        time.sleep(time_to_sleep)

if settings.Get("Console", "HideConsole", False):
    console.RestoreConsole()
    console.CloseConsole()