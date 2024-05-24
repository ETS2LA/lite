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

    def CloseUpaterWindow():
        variables.ROOT.destroy()
        variables.ROOT = None

    import src.uicomponents as uicomponents
    import threading
    import tkinter
    import sv_ttk

    variables.ROOT = tkinter.Tk()
    variables.ROOT.title("ETS2LA-Lite - Updater")
    variables.ROOT.geometry(f"{400}x{200}")
    variables.ROOT.update()
    sv_ttk.set_theme(settings.Get("UI", "Theme", "dark"), variables.ROOT)
    variables.ROOT.protocol("WM_DELETE_WINDOW", CloseUpaterWindow)
    variables.ROOT.resizable(False, False)

    if variables.OS == "nt":
        from ctypes import windll, byref, sizeof, c_int
        variables.HWND = windll.user32.GetParent(variables.ROOT.winfo_id())
        windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int(0x1C1C1C)), sizeof(c_int))
        variables.ROOT.iconbitmap(default=f"{variables.PATH}assets\\favicon.ico")

    uicomponents.MakeLabel(variables.ROOT, "Update Available!", row=1, column=0, sticky="nw", font=("Segoe UI", 12), pady=0)
    uicomponents.MakeLabel(variables.ROOT, "Changelog:", row=2, column=0, sticky="nw", font=("Segoe UI", 10), pady=0)
    uicomponents.MakeLabel(variables.ROOT, changelog, row=3, column=0, sticky="nw", pady=15)

    answer = None
    while answer == None:
        start = time.time()
        variables.ROOT.update()
        time_to_sleep = 1/60 - (time.time() - start)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

    if answer == "Update" and False:
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