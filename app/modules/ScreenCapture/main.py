from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import numpy as np
import traceback
import time
import cv2
import mss

if variables.OS == "nt":
    import win32gui


sct = mss.mss()
if len(sct.monitors) < 2:
    SendCrashReport("ScreenCapture - Only one item in the monitor list, normally there should be at least two.", str(sct.monitors))
    Monitor = sct.monitors[0]
else:
    Monitor = sct.monitors[1]
ScreenX = Monitor["left"]
ScreenY = Monitor["top"]
ScreenWidth = Monitor["width"]
ScreenHeight = Monitor["height"]
LastWindowPosition = 0, ScreenX, ScreenY, ScreenWidth, ScreenHeight


def Initialize():
    global Display
    global Monitor
    global MonitorX1
    global MonitorY1
    global MonitorX2
    global MonitorY2
    global Cam
    global CaptureLibrary

    Display = settings.Get("ScreenCapture", "Display", 0)
    Monitor = sct.monitors[(Display + 1)]
    MonitorX1 = Monitor["left"]
    MonitorY1 = Monitor["top"]
    MonitorX2 = Monitor["width"]
    MonitorY2 = Monitor["height"]
    Cam = None
    CaptureLibrary = None

    try:

        if variables.OS == "nt":

            try:

                from windows_capture import WindowsCapture, Frame, InternalCaptureControl
                capture = WindowsCapture(
                    cursor_capture=False,
                    draw_border=False,
                    monitor_index=Display + 1,
                    window_name=None,
                )
                global WindowsCaptureFrame
                global StopWindowsCapture
                StopWindowsCapture = False
                @capture.event
                def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
                    global WindowsCaptureFrame
                    global StopWindowsCapture
                    WindowsCaptureFrame = frame.convert_to_bgr().frame_buffer.copy()
                    if StopWindowsCapture:
                        StopWindowsCapture = False
                        capture_control.stop()
                @capture.event
                def on_closed():
                    print("Capture Session Closed")
                try:
                    control.stop()
                except:
                    pass
                control = capture.start_free_threaded()

                CaptureLibrary = "WindowsCapture"

            except:

                import bettercam
                try:
                    Cam.stop()
                except:
                    pass
                try:
                    Cam.close()
                except:
                    pass
                try:
                    Cam.release()
                except:
                    pass
                try:
                    del Cam
                except:
                    pass
                Cam = bettercam.create(output_idx=Display, output_color="BGR")
                Cam.start()
                Cam.get_latest_frame()
                CaptureLibrary = "BetterCam"

        else:

            CaptureLibrary = "MSS"

    except:

        CaptureLibrary = "MSS"


def Capture(ImageType:str = "both"):
    """ImageType: "both", "cropped", "full" """

    if CaptureLibrary.lower() == "windowscapture":

        try:

            img = cv2.cvtColor(np.array(WindowsCaptureFrame), cv2.COLOR_BGRA2BGR)
            if ImageType.lower() == "both":
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg, img
            elif ImageType.lower() == "cropped":
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg
            elif ImageType.lower() == "full":
                return img
            else:
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg, img

        except:

            return None if ImageType.lower() == "cropped" or ImageType.lower() == "full" else (None, None)

    elif CaptureLibrary.lower() == "bettercam":

        try:

            if Cam == None:
                Initialize()
            img = np.array(Cam.get_latest_frame())
            if ImageType.lower() == "both":
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg, img
            elif ImageType.lower() == "cropped":
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg
            elif ImageType.lower() == "full":
                return img
            else:
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg, img

        except:

            return None if ImageType.lower() == "cropped" or ImageType.lower() == "full" else (None, None)

    elif CaptureLibrary.lower() == "mss":

        try:

            fullMonitor = sct.monitors[(Display + 1)]
            img = np.array(sct.grab(fullMonitor))
            if ImageType.lower() == "both":
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg, img
            elif ImageType.lower() == "cropped":
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg
            elif ImageType.lower() == "full":
                return img
            else:
                croppedImg = img[MonitorY1:MonitorY2, MonitorX1:MonitorX2]
                return croppedImg, img

        except:

            return None if ImageType.lower() == "cropped" or ImageType.lower() == "full" else (None, None)


def GetScreenDimensions(Display=1):
    try:
        global ScreenX, ScreenY, ScreenWidth, ScreenHeight
        Monitor = sct.monitors[Display]
        ScreenX = Monitor["left"]
        ScreenY = Monitor["top"]
        ScreenWidth = Monitor["width"]
        ScreenHeight = Monitor["height"]
    except:
        SendCrashReport("ScreenCapture - Error in function GetScreenDimensions.", str(traceback.format_exc()))
    return ScreenX, ScreenY, ScreenWidth, ScreenHeight


def GetScreenIndex(X, Y):
    Monitors = sct.monitors
    ClosestScreenIndex = None
    ClosestDistance = float('inf')
    for i, Monitor in enumerate(Monitors[1:]):
        CenterX = (Monitor['left'] + Monitor['left'] + Monitor['width']) // 2
        CenterY = (Monitor['top'] + Monitor['top'] + Monitor['height']) // 2
        Distance = ((CenterX - X) ** 2 + (CenterY - Y) ** 2) ** 0.5
        if Distance < ClosestDistance:
            ClosestScreenIndex = i + 1
            ClosestDistance = Distance
    return ClosestScreenIndex


def ValidateCaptureArea(Display, X1, Y1, X2, Y2):
    Monitor = sct.monitors[Display]
    Width, Height = Monitor["width"], Monitor["height"]
    X1 = max(0, min(Width - 1, X1))
    X2 = max(0, min(Width - 1, X2))
    Y1 = max(0, min(Height - 1, Y1))
    Y2 = max(0, min(Height - 1, Y2))
    if X1 == X2:
        if X1 == 0:
            X2 = Width - 1
        else:
            X1 = 0
    if Y1 == Y2:
        if Y1 == 0:
            Y2 = Height - 1
        else:
            Y1 = 0
    return X1, Y1, X2, Y2


def GetWindowPosition(Name="", Blacklist=[""]):
    global LastWindowPosition
    if variables.OS == "nt":
        if LastWindowPosition[0] + 1 < time.time():
            HWND = None
            TopWindows = []
            Window = LastWindowPosition[1], LastWindowPosition[2], LastWindowPosition[3], LastWindowPosition[4]
            win32gui.EnumWindows(lambda HWND, TopWindows: TopWindows.append((HWND, win32gui.GetWindowText(HWND))), TopWindows)
            for HWND, WindowText in TopWindows:
                if Name in WindowText and all(BlacklistItem not in WindowText for BlacklistItem in Blacklist):
                    RECT = win32gui.GetClientRect(HWND)
                    TopLeft = win32gui.ClientToScreen(HWND, (RECT[0], RECT[1]))
                    BottomRight = win32gui.ClientToScreen(HWND, (RECT[2], RECT[3]))
                    Window = (TopLeft[0], TopLeft[1], BottomRight[0] - TopLeft[0], BottomRight[1] - TopLeft[1])
                    break
            LastWindowPosition = time.time(), Window[0], Window[1], Window[0] + Window[2], Window[1] + Window[3]
            return Window[0], Window[1], Window[0] + Window[2], Window[1] + Window[3]
        else:
            return LastWindowPosition[1], LastWindowPosition[2], LastWindowPosition[3], LastWindowPosition[4]
    else:
        return ScreenX, ScreenY, ScreenX + ScreenWidth, ScreenY + ScreenHeight


def GetRouteAdvisorPosition(Side="Automatic"):
    X1, Y1, X2, Y2 = GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
    DistanceFromRight = 21
    DistanceFromBottom = 100
    Width = 420
    Height = 219
    Scale = (Y2 - Y1) / 1080

    if Side == "Left" or Side == "Automatic":
        X = X1 + (DistanceFromRight * Scale)
        Y = Y1 + (Y2 - Y1) - (DistanceFromBottom * Scale + Height * Scale)
        LeftMapTopLeft = (round(X), round(Y))
        X = X1 + (DistanceFromRight * Scale + Width * Scale)
        Y = Y1 + (Y2 - Y1) - (DistanceFromBottom * Scale)
        LeftMapBottomRight = (round(X), round(Y))
        X = LeftMapBottomRight[0] - (LeftMapBottomRight[0] - LeftMapTopLeft[0]) * 0.57
        Y = LeftMapBottomRight[1] - (LeftMapBottomRight[1] - LeftMapTopLeft[1]) * 0.575
        LeftArrowTopLeft = (round(X), round(Y))
        X = LeftMapBottomRight[0] - (LeftMapBottomRight[0] - LeftMapTopLeft[0]) * 0.43
        Y = LeftMapBottomRight[1] - (LeftMapBottomRight[1] - LeftMapTopLeft[1]) * 0.39
        LeftArrowBottomRight = (round(X), round(Y))
        if Side == "Automatic":
            LeftImage = np.array(sct.grab({"left": LeftMapTopLeft[0], "top": LeftMapTopLeft[1], "width": LeftMapBottomRight[0] - LeftMapTopLeft[0], "height": LeftMapBottomRight[1] - LeftMapTopLeft[1]}))

    if Side == "Right" or Side == "Automatic":
        X = X1 + (X2 - X1) - (DistanceFromRight * Scale + Width * Scale)
        Y = Y1 + (Y2 - Y1) - (DistanceFromBottom * Scale + Height * Scale)
        RightMapTopLeft = (round(X), round(Y))
        X = X1 + (X2 - X1) - (DistanceFromRight * Scale)
        Y = Y1 + (Y2 - Y1) - (DistanceFromBottom * Scale)
        RightMapBottomRight = (round(X), round(Y))
        X = RightMapBottomRight[0] - (RightMapBottomRight[0] - RightMapTopLeft[0]) * 0.57
        Y = RightMapBottomRight[1] - (RightMapBottomRight[1] - RightMapTopLeft[1]) * 0.575
        RightArrowTopLeft = (round(X), round(Y))
        X = RightMapBottomRight[0] - (RightMapBottomRight[0] - RightMapTopLeft[0]) * 0.43
        Y = RightMapBottomRight[1] - (RightMapBottomRight[1] - RightMapTopLeft[1]) * 0.39
        RightArrowBottomRight = (round(X), round(Y))
        if Side == "Automatic":
            RightImage = np.array(sct.grab({"left": RightMapTopLeft[0], "top": RightMapTopLeft[1], "width": RightMapBottomRight[0] - RightMapTopLeft[0], "height": RightMapBottomRight[1] - RightMapTopLeft[1]}))

    if Side == "Automatic":
        # TODO: Classify both images and pick the one where it is more certain that there is a route advisor
        return RightMapTopLeft, RightMapBottomRight, RightArrowTopLeft, RightArrowBottomRight
    elif Side == "Left":
        return LeftMapTopLeft, LeftMapBottomRight, LeftArrowTopLeft, LeftArrowBottomRight
    elif Side == "Right":
        return RightMapTopLeft, RightMapBottomRight, RightArrowTopLeft, RightArrowBottomRight