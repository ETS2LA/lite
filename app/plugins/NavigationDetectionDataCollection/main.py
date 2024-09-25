import modules.ScreenCapture.main as ScreenCapture
import src.variables as variables
import time
import cv2
import os

def Initialize():
    global LastScreenCaptureCheck
    global LastCapture
    LastScreenCaptureCheck = 0
    LastCapture = 0
    ScreenCapture.Initialize()

def Run(data):
    CurrentTime = time.time()

    global LastScreenCaptureCheck
    global LastCapture

    if LastScreenCaptureCheck + 0.5 < CurrentTime:
        MapTopLeft, MapBottomRight, ArrowTopLeft, ArrowBottomRight = ScreenCapture.GetRouteAdvisorPosition()
        ScreenX, ScreenY, _, _ = ScreenCapture.GetScreenDimensions(ScreenCapture.GetScreenIndex((MapTopLeft[0] + MapBottomRight[0]) / 2, (MapTopLeft[1] + MapBottomRight[1]) / 2))
        if ScreenCapture.MonitorX1 != MapTopLeft[0] - ScreenX or ScreenCapture.MonitorY1 != MapTopLeft[1] - ScreenY or ScreenCapture.MonitorX2 != MapBottomRight[0] - ScreenX or ScreenCapture.MonitorY2 != MapBottomRight[1] - ScreenY:
            ScreenIndex = ScreenCapture.GetScreenIndex((MapTopLeft[0] + MapBottomRight[0]) / 2, (MapTopLeft[1] + MapBottomRight[1]) / 2)
            if ScreenCapture.Display != ScreenIndex - 1:
                if ScreenCapture.CaptureLibrary == "WindowsCapture":
                    ScreenCapture.StopWindowsCapture = True
                    while ScreenCapture.StopWindowsCapture == True:
                        time.sleep(0.01)
                ScreenCapture.Initialize()
            ScreenCapture.MonitorX1, ScreenCapture.MonitorY1, ScreenCapture.MonitorX2, ScreenCapture.MonitorY2 = ScreenCapture.ValidateCaptureArea(ScreenIndex, MapTopLeft[0] - ScreenX, MapTopLeft[1] - ScreenY, MapBottomRight[0] - ScreenX, MapBottomRight[1] - ScreenY)
        LastScreenCaptureCheck = CurrentTime

    Frame = ScreenCapture.Capture(ImageType="cropped")
    if type(Frame) == type(None) or Frame.shape[0] <= 0 or Frame.shape[1] <= 0:
        return

    cv2.imshow("NavigationDetectionDataCollection", Frame)
    cv2.waitKey(1)

    variables.QUEUE.put({"MANAGEPLUGINS": ["NavigationDetectionDataCollection", "Restart"]})