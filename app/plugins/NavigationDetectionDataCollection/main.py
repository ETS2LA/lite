import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage
import src.uicomponents as uicomponents
import src.variables as variables
import numpy as np
import keyboard
import time
import cv2
import os


def Initialize():
    global LastScreenCaptureCheck
    global LastCapture

    global MapTopLeft
    global MapBottomRight
    global ArrowTopLeft
    global ArrowBottomRight

    global Enabled
    global Side

    global LastEnabledPressed
    global LastSideSwitchPressed

    LastScreenCaptureCheck = 0
    LastCapture = 0

    MapTopLeft = 0
    MapBottomRight = 0
    ArrowTopLeft = 0
    ArrowBottomRight = 0

    Enabled = False
    Side = "Right"

    LastEnabledPressed = False
    LastSideSwitchPressed = False

    ScreenCapture.Initialize()
    ShowImage.Initialize("Left - NavigationDetectionDataCollection", (0, 0, 0))
    ShowImage.Initialize("Right - NavigationDetectionDataCollection", (0, 0, 0))


def Run(data):
    CurrentTime = time.time()

    global LastScreenCaptureCheck
    global LastCapture

    global MapTopLeft
    global MapBottomRight
    global ArrowTopLeft
    global ArrowBottomRight

    global Enabled
    global Side

    global LastEnabledPressed
    global LastSideSwitchPressed

    SideSwitchPRessed = keyboard.is_pressed("X")
    if LastSideSwitchPressed == False and SideSwitchPRessed == True:
        Side = "Right" if Side == "Left" else "Left"
    LastSideSwitchPressed = SideSwitchPRessed

    EnabledPressed = keyboard.is_pressed("F")
    if LastEnabledPressed == False and EnabledPressed == True:
        Enabled = not Enabled
    LastEnabledPressed = EnabledPressed

    if LastCapture + 0.2 < CurrentTime:
        LastCapture = CurrentTime
        for i in range(2):
            if i == 0:
                CurrentSide = Side
            else:
                CurrentSide = "Left" if Side == "Right" else "Right"

            MapTopLeft, MapBottomRight, ArrowTopLeft, ArrowBottomRight = ScreenCapture.GetRouteAdvisorPosition(CurrentSide)
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

            Name = f"{round(CurrentTime, 2)}-{CurrentSide}".replace(".", "-")
            if os.path.exists(f"{variables.Path}cache/NavigationDetectionDataCollection") == False:
                os.makedirs(f"{variables.Path}cache/NavigationDetectionDataCollection")
            if Enabled:
                cv2.imwrite(f"{variables.Path}cache/NavigationDetectionDataCollection/{Name}.png", Frame)

            if Side == CurrentSide:
                cv2.rectangle(Frame, (0, 0), (Frame.shape[1] -1, Frame.shape[0] - 1), (0, 255, 0) if Enabled else (0, 0, 255), round(Frame.shape[0] * 0.01))

            LowerBlue = np.array([120, 65, 0])
            UpperBlue = np.array([255, 200, 110])
            MaskBlue = cv2.inRange(Frame[ArrowTopLeft[1] - MapTopLeft[1]:ArrowBottomRight[1] - MapBottomRight[1], ArrowTopLeft[0] - MapTopLeft[0]:ArrowBottomRight[0] - MapBottomRight[0]], LowerBlue, UpperBlue)
            ArrowHeight, ArrowWidth = MaskBlue.shape[:2]
            PixelRatio = round(cv2.countNonZero(MaskBlue) / (ArrowWidth * ArrowHeight), 3)

            if Side == CurrentSide:
                if PixelRatio > 0.15 and PixelRatio < 0.23:
                    Label = f"SideCorrect:True,ZoomCorrect:True,TabCorrect:True"
                elif PixelRatio < 0.01:
                    Label = f"SideCorrect:True,ZoomCorrect:False,TabCorrect:False"
                else:
                    Label = f"SideCorrect:True,ZoomCorrect:False,TabCorrect:True"
            else:
                if PixelRatio > 0.15 and PixelRatio < 0.23:
                    Label = f"SideCorrect:False,ZoomCorrect:False,TabCorrect:False"
                elif PixelRatio < 0.01:
                    Label = f"SideCorrect:False,ZoomCorrect:False,TabCorrect:False"
                else:
                    Label = f"SideCorrect:False,ZoomCorrect:False,TabCorrect:False"

            for i in range(len(Label.split(","))):
                text, fontscale, thickness, width, height = uicomponents.GetTextSize(Label.split(",")[i], Frame.shape[1], 15)
                cv2.putText(Frame, text, (5, 25 + (i * 30)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, (255, 255, 255), thickness, cv2.LINE_AA)

            if Enabled:
                with open(f"{variables.Path}cache/NavigationDetectionDataCollection/{Name}.txt", "w") as f:
                    f.write(Label)

            ShowImage.Show(f"{CurrentSide} - NavigationDetectionDataCollection", Frame)