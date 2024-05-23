
import src.variables as variables
import src.settings as settings
import numpy as np
import cv2
import mss

display = settings.Get("ScreenCapture", "display", 0)

def Initialize(CamSetupDisplay:int = display):
    global sct
    global display
    global monitor
    global monitor_x1
    global monitor_y1
    global monitor_x2
    global monitor_y2
    global cam
    global cam_library

    sct = mss.mss()
    display = settings.Get("ScreenCapture", "display", 0)
    monitor = sct.monitors[(display + 1)]
    monitor_x1 = monitor["left"]
    monitor_y1 = monitor["top"]
    monitor_x2 = monitor["width"]
    monitor_y2 = monitor["height"]
    cam = None
    cam_library = None

    if settings.Get("NavigationDetectionAI", "map_topleft", "unset") != "unset" and settings.Get("NavigationDetectionAI", "map_bottomright", "unset") != "unset":
        monitor_x1 = settings.Get("NavigationDetectionAI", "map_topleft", "unset")[0]
        monitor_y1 = settings.Get("NavigationDetectionAI", "map_topleft", "unset")[1]
        monitor_x2 = settings.Get("NavigationDetectionAI", "map_bottomright", "unset")[0]
        monitor_y2 = settings.Get("NavigationDetectionAI", "map_bottomright", "unset")[1]

    try:
        if variables.OS == "nt":
            import bettercam
            try:
                cam.stop()
            except:
                pass
            try:
                cam.close()
            except:
                pass
            try:
                cam.release()
            except:
                pass
            try:
                del cam
            except:
                pass
            cam = bettercam.create(output_idx=CamSetupDisplay)
            cam.start()
            cam.get_latest_frame()
            cam_library = "BetterCam"
        else:
            display = CamSetupDisplay
            cam_library = "MSS"
    except:
        display = CamSetupDisplay
        cam_library = "MSS"


def plugin(imgtype:str = "both"):
    """imgtype: "both", "cropped", "full" """

    if variables.OS == "nt" and cam_library == "BetterCam":
        try:
            if cam == None:
                Initialize(settings.Get("ScreenCapture", "display", 0))
            img = cam.get_latest_frame()
            img = np.array(img)
            if imgtype == "both":
                croppedImg = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return croppedImg, img
            elif imgtype == "cropped":
                croppedImg = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return croppedImg
            elif imgtype == "full":
                return img
            else:
                croppedImg = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return croppedImg, img

        except:

            return (None, None) if imgtype != "cropped" or imgtype != "full" else None

    else:

        try:
            fullMonitor = sct.monitors[(display + 1)]
            img = np.array(sct.grab(fullMonitor))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if imgtype == "both":
                croppedImg = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return croppedImg, img
            elif imgtype == "cropped":
                croppedImg = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return croppedImg
            elif imgtype == "full":
                return img
            else:
                croppedImg = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return croppedImg, img

        except:

            return (None, None) if imgtype != "cropped" or imgtype != "full" else None