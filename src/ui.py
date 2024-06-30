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
    tab_MainMenu.grid_rowconfigure(10, weight=1)
    tabControl.add(tab_MainMenu, text ='MainMenu')

    tab_NavigationDetectionAI = ttk.Frame(tabControl)
    tab_NavigationDetectionAI.grid_columnconfigure(0, weight=2)
    tab_NavigationDetectionAI.grid_rowconfigure(12, weight=1)
    tabControl.add(tab_NavigationDetectionAI, text ='NavigationDetectionAI')

    tab_Steering = ttk.Frame(tabControl)
    tab_Steering.grid_columnconfigure(0, weight=2)
    tabControl.add(tab_Steering, text ='Steering')


    def InitializeMainMenu():
        uicomponents.MakeLabel(tab_MainMenu, "ETS2LA-Lite", row=1, column=0, sticky="n", pady=13, font=("Segoe UI", 15))
        uicomponents.MakeLabel(tab_MainMenu, f"Version {variables.VERSION}", row=2, column=0, sticky="n", pady=0)

        try:
            updateTime = str(variables.LASTUPDATE).split(" ")
            updateTime = updateTime[1:]
            months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct":10, "Nov": 11, "Dec": 12}
            updateTime[0] = months[updateTime[0]]
            updateText = f"{updateTime[1]}.{updateTime[0]}.{updateTime[3]} - {updateTime[2]} "
        except:
            import traceback
            traceback.print_exc()
            updateText = "-- Unknown --"
        uicomponents.MakeLabel(tab_MainMenu, f"Released {updateText}", row=3, column=0, sticky="n", pady=0)

        uicomponents.MakeLabel(tab_MainMenu, "", row=4, column=0, sticky="n", pady=5)
        uicomponents.MakeButton(tab_MainMenu, "Open Main Setup", lambda: setup.OpenMainSetupCallback(), row=5, column=0, sticky="n", pady=5)
        uicomponents.MakeButton(tab_MainMenu, "Open NavigationDetectionAI Setup", lambda: setup.OpenNavigationDetectionAISetupCallback(), row=6, column=0, sticky="n", pady=0, width=29)
        uicomponents.MakeLabel(tab_MainMenu, "", row=7, column=0, sticky="n", pady=5)

        if settings.Get('CrashReports', 'AllowCrashReports') != None:
            if settings.Get('CrashReports', 'AllowCrashReports'):
                uicomponents.MakeLabel(tab_MainMenu, "Crash reporting is enabled.", row=8, column=0, fg="green")
            else:
                uicomponents.MakeLabel(tab_MainMenu, "Crash reporting is disabled.", row=8, column=0, fg="red")
        else:
            uicomponents.MakeLabel(tab_MainMenu, "", row=8, column=0)

        global UserCountLabel
        UserCountLabel = uicomponents.MakeLabel(tab_MainMenu, f"Users online: {'Loading...' if settings.Get('CrashReports', 'AllowCrashReports') == True else 'Please enable crash reporting to fetch user count.'}", row=9, column=0, sticky="s", pady=20, fg="gray")
    InitializeMainMenu()


    uicomponents.MakeLabel(tab_NavigationDetectionAI, "NavigationDetectionAI", row=1, column=0, sticky="nw", font=("Segoe UI", 13))
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

    OffsetSlider = tkinter.Scale(tab_Steering, from_=-5, to=5, resolution=0.01, orient=tkinter.HORIZONTAL, length=580, command=lambda x: settings.Create("Steering", "Offset", OffsetSlider.get()))
    OffsetSlider.set(settings.Get("Steering", "Offset", 0))
    OffsetSlider.grid(row=2, column=0, padx=2, pady=0, columnspan=2, sticky="ne")
    uicomponents.MakeLabel(tab_Steering, "Offset", row=2, column=0, padx=5, pady=22, sticky="nw")

    OffsetSlider = tkinter.Scale(tab_Steering, from_=0, to=10, resolution=1, orient=tkinter.HORIZONTAL, length=580, command=lambda x: settings.Create("Steering", "Smoothness", OffsetSlider.get()))
    OffsetSlider.set(settings.Get("Steering", "Smoothness", 3))
    OffsetSlider.grid(row=3, column=0, padx=2, pady=0, columnspan=2, sticky="ne")
    uicomponents.MakeLabel(tab_Steering, "Smoothness", row=3, column=0, padx=5, pady=22, sticky="nw")

    OffsetSlider = tkinter.Scale(tab_Steering, from_=0.1, to=2, resolution=0.01, orient=tkinter.HORIZONTAL, length=580, command=lambda x: settings.Create("Steering", "Sensitivity", OffsetSlider.get()))
    OffsetSlider.set(settings.Get("Steering", "Sensitivity", 0.5))
    OffsetSlider.grid(row=4, column=0, padx=2, pady=0, columnspan=2, sticky="ne")
    uicomponents.MakeLabel(tab_Steering, "Sensitivity", row=4, column=0, padx=5, pady=22, sticky="nw")

    OffsetSlider = tkinter.Scale(tab_Steering, from_=0, to=1, resolution=0.01, orient=tkinter.HORIZONTAL, length=580, command=lambda x: settings.Create("Steering", "Maximum", OffsetSlider.get()))
    OffsetSlider.set(settings.Get("Steering", "Maximum", 1))
    OffsetSlider.grid(row=5, column=0, padx=2, pady=0, columnspan=2, sticky="ne")
    uicomponents.MakeLabel(tab_Steering, "Max Steering", row=5, column=0, padx=5, pady=22, sticky="nw")

    uicomponents.MakeButton(tab_Steering, "Apply Changes", lambda: NavigationDetectionAI.UpdateSettings(), row=6, column=0, pady=20, sticky="s", width=30)