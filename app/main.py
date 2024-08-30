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

THREADS = []
StopThreads = False
def RunPlugins():
    global THREADS, StopThreads
    while True:
        AnyAlive = False
        for thread in THREADS:
            if thread.is_alive() == True:
                StopThreads = True
                AnyAlive = True
        if AnyAlive == False:
            break
    StopThreads = False
    THREADS = []

    import plugins.NavigationDetectionAI.main as NavigationDetectionAI
    def NavigationDetectionAIThread():
        global FPS, StopThreads
        NavigationDetectionAI.Initialize()
        while variables.BREAK == False and StopThreads == False:
            start = time.time()
            NavigationDetectionAI.plugin()
            end = time.time()
            FPS = (1 / (end - start)) if end - start > 0 else 1000
    #THREADS.append(threading.Thread(target=NavigationDetectionAIThread, daemon=True))
    #THREADS[-1].start()

    import plugins.NavigationDetectionV4.main as NavigationDetectionV4
    def NavigationDetectionV4Thread():
        global FPS, StopThreads
        NavigationDetectionV4.Initialize()
        while variables.BREAK == False and StopThreads == False:
            start = time.time()
            NavigationDetectionV4.plugin()
            end = time.time()
            FPS = (1 / (end - start)) if end - start > 0 else 1000
    THREADS.append(threading.Thread(target=NavigationDetectionV4Thread, daemon=True))
    THREADS[-1].start()
RunPlugins()

FPS = 0
FPS_UpdateTime = 0
MainMenu_UpdateTime = 0

DEVMODE = True
if DEVMODE:
    import hashlib
    Scripts = []
    Scripts.append(("Main", f"{variables.PATH}app/main.py"))
    for Object in os.listdir(f"{variables.PATH}app/plugins"):
        Scripts.append((Object, f"{variables.PATH}app/plugins/{Object}/main.py"))
    for Object in os.listdir(f"{variables.PATH}app/src"):
        Scripts.append((Object, f"{variables.PATH}app/src/{Object}"))
    LastScripts = {}
    for i, (Script, Path) in enumerate(Scripts):
        try:
            hash = hashlib.md5(open(Path, "rb").read()).hexdigest()
            LastScripts[i] = hash
        except:
            pass

while variables.BREAK == False:
    start = time.time()

    if DEVMODE:
        for i, (Script, Path) in enumerate(Scripts):
            try:
                hash = hashlib.md5(open(Path, "rb").read()).hexdigest()
                if hash != LastScripts[i]:
                    variables.POPUP = [f"Reloading {Script}...", 0, 0.5]
                    LastScripts[i] = hash
                    RunPlugins()
                    break
            except:
                pass

    ui.Update()

    time_to_sleep = 1/60 - (time.time() - start)
    if time_to_sleep > 0:
        time.sleep(time_to_sleep)

if settings.Get("Console", "HideConsole", False):
    console.RestoreConsole()
    console.CloseConsole()