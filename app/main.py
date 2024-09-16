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

def PluginProcessFunction(PluginName, Queue):
    variables.QUEUE = Queue
    Plugin = __import__(f"plugins.{PluginName}.main", fromlist=[""])
    Plugin.Initialize()
    while variables.BREAK == False:
        Plugin.plugin()
        while variables.QUEUE.empty() == False:
            Queue.put(variables.QUEUE.get())

def RunPlugins(Plugin=None, Action=None):
    global PluginProcesses, PluginQueue
    if "PluginProcesses" not in globals():
        PluginProcesses = []
    if "PluginQueue" not in globals():
        PluginQueue = multiprocessing.Queue()
    if Plugin != None and Action != None:
        if Action == "Restart":
            if not any(process.name == Plugin for process in PluginProcesses):
                return
        if Action == "Stop" or Action == "Restart":
            for i, process in enumerate(PluginProcesses):
                if process.name == Plugin:
                    process.terminate()
                    PluginProcesses.pop(i)
                    break
        if "PluginProcesses" not in globals():
            PluginProcesses = []
        if "PluginQueue" not in globals():
            PluginQueue = multiprocessing.Queue()
        if Action == "Start" or Action == "Restart":
            PluginProcesses.append(multiprocessing.Process(target=PluginProcessFunction, args=(Plugin, PluginQueue), name=Plugin, daemon=True))
            PluginProcesses[-1].start()
        return
    if "PluginProcesses" in globals():
        for PluginProcess in PluginProcesses:
            PluginProcess.terminate()
    for Plugin in os.listdir(f"{variables.PATH}app/plugins"):
        if Plugin not in variables.INVISIBLE_PLUGINS:
            variables.AVAILABLE_PLUGINS.append(Plugin)
            if os.path.isdir(f"{variables.PATH}app/plugins/{Plugin}") and settings.Get("EnabledPlugins", Plugin, True):
                PluginProcesses.append(multiprocessing.Process(target=PluginProcessFunction, args=(Plugin, PluginQueue), name=Plugin, daemon=True))
    for PluginProcess in PluginProcesses:
        PluginProcess.start()

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

    RunPlugins()

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
                            RunPlugins()
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