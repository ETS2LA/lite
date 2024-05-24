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
if remote_version != variables.VERSION:
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
    variables.ROOT.geometry(f"{450}x{250}")
    variables.ROOT.update()
    sv_ttk.set_theme(settings.Get("UI", "Theme", "dark"), variables.ROOT)
    variables.ROOT.protocol("WM_DELETE_WINDOW", CloseUpaterWindow)
    variables.ROOT.resizable(False, False)

    if variables.OS == "nt":
        from ctypes import windll, byref, sizeof, c_int
        variables.HWND = windll.user32.GetParent(variables.ROOT.winfo_id())
        windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int(0x1C1C1C)), sizeof(c_int))
        variables.ROOT.iconbitmap(default=f"{variables.PATH}assets\\favicon.ico")

    variables.ROOT.grid_rowconfigure(3, weight=1)
    variables.ROOT.grid_columnconfigure(0, weight=1)

    uicomponents.MakeLabel(variables.ROOT, "Update Available!", row=1, column=0, sticky="nw", font=("Segoe UI", 13), pady=0)
    uicomponents.MakeLabel(variables.ROOT, "Changelog:", row=2, column=0, sticky="nw", font=("Segoe UI", 11), pady=0)
    uicomponents.MakeLabel(variables.ROOT, str("\n".join([changelog[i:i+72] for i in range(0, len(changelog), 72)])).replace("\n ", "\n"), row=3, column=0, sticky="nw", columnspan=2, pady=15)

    answer = None

    def Update_Callback():
        global answer
        answer = "Update"
    OpenMainSetupButton = uicomponents.MakeButton(variables.ROOT, "Update", lambda: Update_Callback(), row=4, column=0, sticky="sw")

    def DoNotUpdate_Callback():
        global answer
        answer = "DoNotUpdate"
    OpenMainSetupButton = uicomponents.MakeButton(variables.ROOT, "Do Not Update", lambda: DoNotUpdate_Callback(), row=4, column=1, sticky="se")

    while answer == None:
        start = time.time()
        variables.ROOT.update()
        time_to_sleep = 1/60 - (time.time() - start)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

    if answer == "Update":
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