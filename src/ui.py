import src.uicomponents as uicomponents
import src.variables as variables
import src.settings as settings
import src.console as console

from tkinter import ttk
import threading
import tkinter
import sv_ttk

def initialize():
    width = settings.Get("UI", "Width", 700)
    height = settings.Get("UI", "Height", 400)
    x = settings.Get("UI", "X", 0)
    y = settings.Get("UI", "Y", 0)
    theme = settings.Get("UI", "Theme", "dark")
    resizable = settings.Get("UI", "Resizable", False)

    if variables.OS == "nt":
        from ctypes import windll, byref, sizeof, c_int

    variables.ROOT = tkinter.Tk()
    variables.ROOT.title("ETS2LA-Lite")
    variables.ROOT.geometry(f"{width}x{height}+{x}+{y}")
    variables.ROOT.update()
    sv_ttk.set_theme(theme, variables.ROOT)
    variables.ROOT.protocol("WM_DELETE_WINDOW", close)
    variables.ROOT.resizable(resizable, resizable)

    if variables.OS == "nt":
        variables.HWND = windll.user32.GetParent(variables.ROOT.winfo_id())
        windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int(0x2F2F2F)), sizeof(c_int))
        variables.ROOT.iconbitmap(default=f"{variables.PATH}assets\\favicon.ico")

def close():
    settings.Create("UI", "Width", variables.ROOT.winfo_width())
    settings.Create("UI", "Height", variables.ROOT.winfo_height())
    settings.Create("UI", "X", variables.ROOT.winfo_x())
    settings.Create("UI", "Y", variables.ROOT.winfo_y())
    console.RestoreConsole()
    console.CloseConsole()
    variables.ROOT.destroy()
    variables.BREAK = True

def createUI():
    style = ttk.Style()
    style.layout("Tab",[('Notebook.tab',{'sticky':'nswe','children':[('Notebook.padding',{'side':'top','sticky':'nswe','children':[('Notebook.label',{'side':'top','sticky':''})],})],})])

    tabControl = ttk.Notebook(variables.ROOT)
    tabControl.pack(expand = 1, fill ="both")

    tab_MainMenu = ttk.Frame(tabControl)
    tab_MainMenu.grid_columnconfigure(0, weight=2)
    tabControl.add(tab_MainMenu, text ='MainMenu')

    tab_NavigationDetectionAI = ttk.Frame(tabControl)
    tabControl.add(tab_NavigationDetectionAI, text ='NavigationDetectionAI')

    tab_Steering = ttk.Frame(tabControl)
    tabControl.add(tab_Steering, text ='Steering')


    uicomponents.MakeLabel(tab_MainMenu, "ETS2LA-Lite", row=1, column=0, sticky="n", font=("Segoe UI", 15))
    uicomponents.MakeLabel(tab_MainMenu, f"Version {variables.VERSION}", row=2, column=0, sticky="n", pady=0)

    def OpenMainSetupCallback():
        def OpenMainSetupThread():
            pass
        threading.Thread(target=OpenMainSetupThread, daemon=True).start()
    OpenMainSetupButton = uicomponents.MakeButton(tab_MainMenu, "Open Main Setup", lambda: OpenMainSetupCallback(), row=4, column=0, sticky="n", pady=10)