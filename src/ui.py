import plugins.NavigationDetectionAI.main as NavigationDetectionAI
import src.uicomponents as uicomponents
import src.variables as variables
import src.settings as settings
import src.console as console
import src.setup as setup

from tkinter import ttk
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
    try:
        variables.ROOT.destroy()
    except:
        pass
    variables.BREAK = True

def createUI():
    global InitializeMainMenu
    global tab_MainMenu

    style = ttk.Style()
    style.layout("Tab",[('Notebook.tab',{'sticky':'nswe','children':[('Notebook.padding',{'side':'top','sticky':'nswe','children':[('Notebook.label',{'side':'top','sticky':''})],})],})])

    tabControl = ttk.Notebook(variables.ROOT)
    tabControl.pack(expand = 1, fill ="both")

    tab_MainMenu = ttk.Frame(tabControl)
    tab_MainMenu.grid_columnconfigure(0, weight=2)
    tabControl.add(tab_MainMenu, text ='Main Menu')

    tab_NavigationDetectionAI = ttk.Frame(tabControl)
    tab_NavigationDetectionAI.grid_columnconfigure(0, weight=2)
    tab_NavigationDetectionAI.grid_rowconfigure(12, weight=1)
    tabControl.add(tab_NavigationDetectionAI, text ='Navigation Detection AI')

    tab_Steering = ttk.Frame(tabControl)
    tab_Steering.grid_columnconfigure(0, weight=2)
    tabControl.add(tab_Steering, text ='Steering')


    def InitializeMainMenu():
        uicomponents.MakeLabel(tab_MainMenu, "ETS2LA-Lite", row=1, column=0, sticky="n", font=("Segoe UI", 15))
        uicomponents.MakeLabel(tab_MainMenu, f"Version {variables.VERSION}", row=2, column=0, sticky="n", pady=0)

        uicomponents.MakeButton(tab_MainMenu, "Open Main Setup", lambda: setup.OpenMainSetupCallback(), row=4, column=0, sticky="n", pady=30)
        uicomponents.MakeButton(tab_MainMenu, "Open NavigationDetectionAI Setup", lambda: setup.OpenNavigationDetectionAISetupCallback(), row=5, column=0, sticky="n", pady=0, width=29)
    InitializeMainMenu()


    uicomponents.MakeLabel(tab_NavigationDetectionAI, "Navigation Detection AI", row=1, column=0, sticky="nw", font=("Segoe UI", 13))
    global tab_NavigationDetectionAI_FPS
    tab_NavigationDetectionAI_FPS = uicomponents.MakeLabel(tab_NavigationDetectionAI, "FPS: --", row=1, column=0, sticky="ne", font=("Segoe UI", 13))

    uicomponents.MakeLabel(tab_NavigationDetectionAI, "AI model properties:", row=2, column=0, sticky="nw", pady=10, font=("Segoe UI", 12))
    uicomponents.MakeLabel(tab_NavigationDetectionAI, f"Epochs: {NavigationDetectionAI.GetAIModelProperties()[0]}", row=3, column=0, sticky="nw", font=("Segoe UI", 10))
    uicomponents.MakeLabel(tab_NavigationDetectionAI, f"Batch Size: {NavigationDetectionAI.GetAIModelProperties()[1]}", row=4, column=0, sticky="nw", font=("Segoe UI", 10))
    uicomponents.MakeLabel(tab_NavigationDetectionAI, f"Image Width: {NavigationDetectionAI.GetAIModelProperties()[2]}", row=4, column=0, sticky="nw", font=("Segoe UI", 10))
    uicomponents.MakeLabel(tab_NavigationDetectionAI, f"Image Height: {NavigationDetectionAI.GetAIModelProperties()[3]}", row=5, column=0, sticky="nw", font=("Segoe UI", 10))
    uicomponents.MakeLabel(tab_NavigationDetectionAI, f"Images/Data Points: {NavigationDetectionAI.GetAIModelProperties()[4]}", row=6, column=0, sticky="nw", font=("Segoe UI", 10))
    uicomponents.MakeLabel(tab_NavigationDetectionAI, f"Training Time: {NavigationDetectionAI.GetAIModelProperties()[5]}", row=7, column=0, sticky="nw", font=("Segoe UI", 10))
    uicomponents.MakeLabel(tab_NavigationDetectionAI, f"Training Date: {NavigationDetectionAI.GetAIModelProperties()[6]}", row=8, column=0, sticky="nw", font=("Segoe UI", 10))

    global progresslabel
    global progress
    progresslabel = uicomponents.MakeLabel(tab_NavigationDetectionAI, "Loading...", 12, 0, sticky="sw")
    progress = ttk.Progressbar(tab_NavigationDetectionAI, orient="horizontal", length=268, mode="determinate")
    progress.grid(row=13, column=0, sticky="sw", padx=5, pady=0)

    def CheckForAIUpdates():
        NavigationDetectionAI.CheckForAIModelUpdates()
        while NavigationDetectionAI.AIModelUpdateThread.is_alive(): NavigationDetectionAI.time.sleep(0.1)
        if NavigationDetectionAI.TorchAvailable == True:
            NavigationDetectionAI.LoadAIModel()
        else:
            print("NavigationDetectionAI not available due to missing dependencies.")
            console.RestoreConsole()

    uicomponents.MakeButton(tab_NavigationDetectionAI, "Check for AI Model Updates", lambda: CheckForAIUpdates(), row=14, column=0, sticky="sw", width=30)


    uicomponents.MakeLabel(tab_Steering, "Steering", row=1, column=0, sticky="nw", font=("Segoe UI", 13))
    global tab_Steering_FPS
    tab_Steering_FPS = uicomponents.MakeLabel(tab_Steering, "FPS: --", row=1, column=0, sticky="ne", font=("Segoe UI", 13))