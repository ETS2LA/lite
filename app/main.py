import src.translate as translate
import src.variables as variables
import src.settings as settings
import src.console as console
import src.helpers as helpers
import src.plugins as plugins
import src.updater as updater
import src.server as server
import src.ui as ui

import time
import sys
import os


if __name__ == '__main__':
    os.system("cls" if variables.OS == "nt" else "clear")
    print("\nETS2LA-Lite\n-----------\n")

    if "--dev" in sys.argv:
        variables.DEVMODE = True

    if settings.Get("Console", "HideConsole", False):
        console.HideConsole()

    translate.Initialize()
    plugins.ManagePlugins(Plugin="All", Action="Start")
    ui.Initialize()
    updater.CheckForUpdates()
    helpers.RunEvery(60, lambda: server.Ping())
    helpers.RunEvery(60, lambda: server.GetUserCount())

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

        plugins.ManageQueues()

        if variables.DEVMODE:
            for i, (Script, Path) in enumerate(Scripts):
                try:
                    hash = hashlib.md5(open(Path, "rb").read()).hexdigest()
                    if hash != LastScripts[i]:
                        if "plugins" in Path:
                            plugins.ManagePlugins(Plugin=Script, Action="Restart")
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