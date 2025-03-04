import src.variables as variables
import src.settings as settings

import ImageUI
import shutil
import winreg
import os


def GetGamePaths():
    SteamPath = str(winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Valve\\Steam"), "SteamPath")[0])
    SteamPath = SteamPath.replace("\\", "/")
    if SteamPath[-1] != "/": SteamPath += "/"

    DefaultETS2Path = f"{SteamPath}steamapps/common/Euro Truck Simulator 2"
    DefaultATSPath = f"{SteamPath}steamapps/common/American Truck Simulator"

    ETS2Path = settings.Get("Setup", "ETS2Path", DefaultETS2Path if os.path.exists(DefaultETS2Path) else "")
    ATSPath = settings.Get("Setup", "ATSPath", DefaultATSPath if os.path.exists(DefaultATSPath) else "")

    ETS2Path = ETS2Path.replace("\\", "/")
    if len(ETS2Path) > 0 and ETS2Path[-1] != "/": ETS2Path += "/"

    ATSPath = ATSPath.replace("\\", "/")
    if len(ATSPath) > 0 and ATSPath[-1] != "/": ATSPath += "/"

    variables.ETS2Path = ETS2Path
    variables.ATSPath = ATSPath

    GamePaths = []

    if os.path.exists(os.path.join(ETS2Path, "bin/win_x64")):
        GamePaths.append(ETS2Path)

    if os.path.exists(os.path.join(ATSPath, "bin/win_x64")):
        GamePaths.append(ATSPath)

    Reason = ""
    if os.path.exists(os.path.join(ETS2Path, "bin/win_x64")) == False and ETS2Path != "" and os.path.exists(os.path.join(ATSPath, "bin/win_x64")) == False and ATSPath != "":
        Reason = "Invalid ETS2 and ATS paths!"
    elif os.path.exists(os.path.join(ETS2Path, "bin/win_x64")) == False and ETS2Path != "":
        Reason = "Invalid ETS2 path!"
    elif os.path.exists(os.path.join(ATSPath, "bin/win_x64")) == False and ATSPath != "":
        Reason = "Invalid ATS path!"

    if Reason != "":
        Top = 0
        Right = variables.WindowWidth - 1
        ImageUI.Popup(Reason,
                      StartX1=Right * 0.3,
                      StartY1=Top + 20,
                      StartX2=Right * 0.7,
                      StartY2=Top,
                      EndX1=Right * 0.2,
                      EndY1=Top + 60,
                      EndX2=Right * 0.8,
                      EndY2=Top + 100,
                      ShowDuration=15)

        variables.Page = "GamePathInput"

    return GamePaths


def CheckDLLs():
    GamePaths = GetGamePaths()
    DLLsCopied = True
    for GamePath in GamePaths:
        if os.path.exists(f"{GamePath}bin/win_x64/plugins") == False: DLLsCopied = False
        if os.path.isfile(f"{GamePath}bin/win_x64/plugins/ets2_la_plugin.dll") == False: DLLsCopied = False
        if os.path.isfile(f"{GamePath}bin/win_x64/plugins/scs_sdk_controller.dll") == False: DLLsCopied = False
        if os.path.isfile(f"{GamePath}bin/win_x64/plugins/scs-telemetry.dll") == False: DLLsCopied = False
    return DLLsCopied


def CopyDLLs():
    GamePaths = GetGamePaths()
    AnyCopied = False
    for GamePath in GamePaths:
        try:
            if os.path.exists(f"{GamePath}bin/win_x64/plugins") == False:
                os.makedirs(f"{GamePath}bin/win_x64/plugins")
                AnyCopied = True
        except:
            pass

        try:
            if os.path.exists(f"{GamePath}bin/win_x64/plugins") and os.path.exists(f"{GamePath}bin/win_x64/plugins/ets2_la_plugin.dll") == False:
                shutil.copy2(f"{variables.Path}app/assets/DLLs/ets2_la_plugin.dll", f"{GamePath}bin/win_x64/plugins/ets2_la_plugin.dll")
                AnyCopied = True
        except:
            pass

        try:
            if os.path.exists(f"{GamePath}bin/win_x64/plugins") and os.path.exists(f"{GamePath}bin/win_x64/plugins/scs_sdk_controller.dll") == False:
                shutil.copy2(f"{variables.Path}app/assets/DLLs/scs_sdk_controller.dll", f"{GamePath}bin/win_x64/plugins/scs_sdk_controller.dll")
                AnyCopied = True
        except:
            pass

        try:
            if os.path.exists(f"{GamePath}bin/win_x64/plugins") and os.path.exists(f"{GamePath}bin/win_x64/plugins/scs-telemetry.dll") == False:
                shutil.copy2(f"{variables.Path}app/assets/DLLs/scs-telemetry.dll", f"{GamePath}bin/win_x64/plugins/scs-telemetry.dll")
                AnyCopied = True
        except:
            pass

    if AnyCopied:
        Right = variables.WindowWidth - 1
        Bottom = variables.WindowHeight - 1
        ImageUI.Popup("Copied DDLs into the following game paths:\n" + "\n".join(GamePaths),
                      StartX1=Right * 0.25,
                      StartY1=Bottom,
                      StartX2=Right * 0.75,
                      StartY2=Bottom + 20 + (5 * len(GamePaths)),
                      EndX1=Right * 0.1,
                      EndY1=Bottom - 50 - (15 * len(GamePaths)),
                      EndX2=Right * 0.9,
                      EndY2=Bottom - 10,
                      ShowDuration=15)