import src.variables as variables
import src.settings as settings
import src.console as console
import src.helpers as helpers
import src.server as server
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
        global answer
        answer = "DoNotUpdate"
        try:
            variables.ROOT.destroy()
        except:
            pass
        variables.ROOT = None

    import src.uicomponents as uicomponents
    import threading
    import tkinter
    import sv_ttk

    variables.ROOT = tkinter.Tk()
    variables.ROOT.title("ETS2LA-Lite - Updater")
    variables.ROOT.geometry(f"{450}x{250}+{int(settings.Get('UI', 'X', 0) + settings.Get('UI', 'Width', 700) / 2 - 225)}+{int(settings.Get('UI', 'Y', 0))}")
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
        print("Updating...")
    OpenMainSetupButton = uicomponents.MakeButton(variables.ROOT, "Update", lambda: Update_Callback(), row=4, column=0, sticky="sw")

    def DoNotUpdate_Callback():
        global answer
        answer = "DoNotUpdate"
        print("Skipping update...")
    OpenMainSetupButton = uicomponents.MakeButton(variables.ROOT, "Do Not Update", lambda: DoNotUpdate_Callback(), row=4, column=1, sticky="se")

    while answer == None:
        start = time.time()
        try:
            variables.ROOT.update()
        except:
            pass
        time_to_sleep = 1/60 - (time.time() - start)
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

    if answer == "Update":
        try:
            os.chdir(variables.PATH)
            os.system("git stash")
            os.system("git pull")
        except Exception as e:
            print("Failed to update: " + str(e))
    CloseUpaterWindow()
else:
    print("No update available, current version: " + variables.VERSION)

helpers.RunEvery(60, lambda: server.Ping())
def SetMainMenuUserCount():
    ui.UserCountLabel.set(f"Users online: {server.GetUserCount()}")
    ui.UserCountLabel.update()
if settings.Get("CrashReports", "AllowCrashReports"):
    helpers.RunEvery(300, lambda: SetMainMenuUserCount())

ui.initialize()
ui.createUI()

import plugins.NavigationDetectionAI.main as NavigationDetectionAI
def run_thread():
    global FPS
    NavigationDetectionAI.Initialize()
    while variables.BREAK == False:
        FPS = NavigationDetectionAI.plugin()

threading.Thread(target=run_thread, daemon=True).start()


FPS = 0
FPS_UpdateTime = 0

while variables.BREAK == False:
    start = time.time()

    try:
        ui.progresslabel.config(text=str(NavigationDetectionAI.LoadAILabel))
        ui.progress["value"] = float(NavigationDetectionAI.LoadAIProgress)
    except:
        pass

    if FPS_UpdateTime + 1 < time.time():
        ui.tab_NavigationDetectionAI_FPS.config(text="FPS: " + str(round(FPS, 1)))
        ui.tab_NavigationDetectionAI_FPS.update()
        ui.tab_Steering_FPS.config(text="FPS: " + str(round(FPS, 1)))
        ui.tab_Steering_FPS.update()
        FPS_UpdateTime = time.time()

    variables.ROOT.update()

    time_to_sleep = 1/60 - (time.time() - start)
    if time_to_sleep > 0:
        time.sleep(time_to_sleep)


if settings.Get("Console", "HideConsole", False):
    console.RestoreConsole()