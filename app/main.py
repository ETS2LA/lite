import src.translate as translate
import src.variables as variables
import src.settings as settings
import src.console as console
import src.helpers as helpers
import src.updater as updater
import src.server as server
import src.ui as ui

import multiprocessing
import threading
import time
import sys
import os

def RunNavigationDetectionAI(Queue):
    variables.QUEUE = Queue
    import plugins.NavigationDetectionAI.main as NavigationDetectionAI
    NavigationDetectionAI.Initialize()
    while variables.BREAK == False:
        NavigationDetectionAI.plugin()
        while variables.QUEUE.empty() == False:
           Queue.put(variables.QUEUE.get())

def RunNavigationDetectionV4(Queue):
    variables.QUEUE = Queue
    import plugins.NavigationDetectionV4.main as NavigationDetectionV4
    NavigationDetectionV4.Initialize()
    while variables.BREAK == False:
        NavigationDetectionV4.plugin()
        while variables.QUEUE.empty() == False:
           Queue.put(variables.QUEUE.get())

def RunAdaptiveCruiseControl(Queue):
    variables.QUEUE = Queue
    import plugins.AdaptiveCruiseControl.main as AdaptiveCruiseControl
    AdaptiveCruiseControl.Initialize()
    while variables.BREAK == False:
        AdaptiveCruiseControl.plugin()
        while variables.QUEUE.empty() == False:
           Queue.put(variables.QUEUE.get())

if __name__ == '__main__':
    os.system("cls" if variables.OS == "nt" else "clear")
    print("\nETS2LA-Lite\n-----------\n")

    if "--dev" in sys.argv:
        variables.DEVMODE = True

    if settings.Get("Console", "HideConsole", False):
        console.HideConsole()

    translate.Initialize()
    ui.Initialize()
    updater.CheckForUpdates()
    helpers.RunEvery(60, lambda: server.Ping())
    helpers.RunEvery(60, lambda: server.GetUserCount())

    PluginProcesses = []
    PluginQueue = multiprocessing.Queue()
    #PluginProcesses.append(multiprocessing.Process(target=RunNavigationDetectionAI, args=(PluginQueue,), daemon=True))
    #PluginProcesses.append(multiprocessing.Process(target=RunNavigationDetectionV4, args=(PluginQueue,), daemon=True))
    PluginProcesses.append(multiprocessing.Process(target=RunAdaptiveCruiseControl, args=(PluginQueue,), daemon=True))
    for PluginProcess in PluginProcesses:
        PluginProcess.start()

    FPS = 0
    FPS_UpdateTime = 0
    MainMenu_UpdateTime = 0

    if variables.DEVMODE:
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

        if PluginQueue.empty() == False:
            variables.POPUP = PluginQueue.get()
            while PluginQueue.empty() == False:
                PluginQueue.get()

        if variables.DEVMODE:
            for i, (Script, Path) in enumerate(Scripts):
                try:
                    hash = hashlib.md5(open(Path, "rb").read()).hexdigest()
                    if hash != LastScripts[i]:
                        variables.POPUP = [f"Reloading {Script}...", 0, 0.5]
                        if "plugins" in Path:
                            for PluginProcess in PluginProcesses:
                                PluginProcess.terminate()
                            PluginProcesses = []
                            PluginQueue = multiprocessing.Queue()
                            #PluginProcesses.append(multiprocessing.Process(target=RunNavigationDetectionAI, args=(PluginQueue,), daemon=True))
                            #PluginProcesses.append(multiprocessing.Process(target=RunNavigationDetectionV4, args=(PluginQueue,), daemon=True))
                            PluginProcesses.append(multiprocessing.Process(target=RunAdaptiveCruiseControl, args=(PluginQueue,), daemon=True))
                            for PluginProcess in PluginProcesses:
                                PluginProcess.start()
                        else:
                            ui.Restart()
                        LastScripts[i] = hash
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