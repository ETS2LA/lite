from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import numpy as np
import traceback
import cv2
import mss


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
LastGamePosition = 0, ScreenX, ScreenY, ScreenWidth, ScreenHeight


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


def GetScreenDimensions(monitor=1):
    try:
        global screen_x, screen_y, screen_width, screen_height
        monitor = sct.monitors[monitor]
        screen_x = monitor["left"]
        screen_y = monitor["top"]
        screen_width = monitor["width"]
        screen_height = monitor["height"]
    except:
        SendCrashReport("ScreenCapture - Error in function GetScreenDimensions.", str(traceback.format_exc()))
    return screen_x, screen_y, screen_width, screen_height