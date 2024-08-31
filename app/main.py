import multiprocessing.process
import src.variables as variables
import src.settings as settings
import src.console as console
import src.helpers as helpers
import src.updater as updater
import src.server as server
import src.ui as ui

import multiprocessing
import time
import os

def RunPlugins():
    import plugins.NavigationDetectionV4.main as NavigationDetectionV4
    NavigationDetectionV4.Initialize()
    while variables.BREAK == False:
        NavigationDetectionV4.plugin()

if __name__ == '__main__':
    os.system("cls" if variables.OS == "nt" else "clear")
    print("\nETS2LA-Lite\n-----------\n")

    if settings.Get("Console", "HideConsole", False):
        console.HideConsole()

    ui.Initialize()
    updater.CheckForUpdates()
    helpers.RunEvery(60, lambda: server.Ping())
    server.variables.USERCOUNT = server.GetUserCount()

    PluginProcess = multiprocessing.Process(target=RunPlugins, daemon=True)
    PluginProcess.start()

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
                        PluginProcess.terminate()
                        PluginProcess = multiprocessing.Process(target=RunPlugins, daemon=True)
                        PluginProcess.start()
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