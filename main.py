import src.variables as variables
import src.settings as settings
import src.console as console
import src.ui as ui

import threading
import time


if settings.Get("Console", "HideConsole", False):
    console.HideConsole()

ui.initialize()
ui.createUI()


def run_thread():
    import plugins.NavigationDetectionAI.main as NavigationDetectionAI
    NavigationDetectionAI.Initialize()
    while variables.BREAK == False:
        NavigationDetectionAI.plugin()

threading.Thread(target=run_thread).start()


while variables.BREAK == False:
    
    start = time.time()

    variables.ROOT.update()

    time_to_sleep = 1/60 - (time.time() - start)
    if time_to_sleep > 0:
        time.sleep(time_to_sleep)


if settings.Get("Console", "HideConsole", False):
    console.RestoreConsole()