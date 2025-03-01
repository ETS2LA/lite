import os
import sys
sys.path.append(os.path.dirname(__file__))

import src.variables as variables
import src.settings as settings
import src.console as console
import src.helpers as helpers
import src.plugins as plugins
import src.updater as updater
import src.server as server
import src.ui as ui

import time


if __name__ == '__main__':
    os.system("cls")
    print("\nETS2LA-Lite\n-----------\n")

    if "--dev" in sys.argv:
        variables.DevelopmentMode = True

    if os.path.exists(f"{variables.Path}cache") == False:
        os.makedirs(f"{variables.Path}cache")

    if settings.Get("Console", "HideConsole", False):
        console.HideConsole()

    plugins.Initialize()
    plugins.ManagePlugins(Plugin="All", Action="Start")
    ui.Initialize()
    updater.CheckForUpdates()
    helpers.RunEvery(60, lambda: server.Ping())
    helpers.RunEvery(60, lambda: server.GetUserCount())

    if variables.DevelopmentMode:
        import hashlib
        Scripts = []
        Scripts.append(("Main", f"{variables.Path}app/main.py"))
        for Object in os.listdir(f"{variables.Path}app/plugins"):
            Scripts.append((Object, f"{variables.Path}app/plugins/{Object}/main.py"))
        for Object in os.listdir(f"{variables.Path}app/modules"):
            Scripts.append((Object, f"{variables.Path}app/modules/{Object}/main.py"))
        for Object in os.listdir(f"{variables.Path}app/src"):
            Scripts.append((Object, f"{variables.Path}app/src/{Object}"))
        LastScripts = {}
        for i, (Script, Path) in enumerate(Scripts):
            try:
                Hash = hashlib.md5(open(Path, "rb").read()).hexdigest()
                LastScripts[i] = Hash
            except:
                pass

    while variables.Break == False:
        Start = time.time()

        plugins.ManageSharedMemory()

        if variables.DevelopmentMode:
            for i, (Script, Path) in enumerate(Scripts):
                try:
                    Hash = hashlib.md5(open(Path, "rb").read()).hexdigest()
                    if Hash != LastScripts[i]:
                        if "plugins" in os.path.dirname(Path):
                            os.system("cls")
                            print("\nETS2LA-Lite\n-----------\n")
                            plugins.ManagePlugins(Plugin=Script, Action="Restart")
                        elif "modules" in os.path.dirname(Path):
                            os.system("cls")
                            print("\nETS2LA-Lite\n-----------\n")
                            plugins.ManagePlugins(Plugin="All", Action="Restart")
                        else:
                            ui.Restart()
                        LastScripts[i] = Hash
                        break
                except:
                    pass

        ui.Update()

        TimeToSleep = 1/60 - (time.time() - Start)
        if TimeToSleep > 0:
            time.sleep(TimeToSleep)

    if settings.Get("Console", "HideConsole", False):
        console.RestoreConsole()
        console.CloseConsole()