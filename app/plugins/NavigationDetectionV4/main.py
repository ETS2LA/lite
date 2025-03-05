from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from modules.SDKController.main import SCSController
import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage
import src.variables as variables
import src.settings as settings
import numpy as np
import traceback
import keyboard
import time
import cv2

global Enabled
Enabled = True

def Initialize():
    global EnableKey
    global EnableKeyPressed
    global LastEnableKeyPressed
    global LastScreenCaptureCheck

    global SteeringOffset
    global SteeringSmoothness
    global SteeringSensitivity
    global SteeringMaximum

    global SDKController
    global TruckSimAPI

    EnableKey = settings.Get("Controls", "Steering", "n")
    EnableKeyPressed = False
    LastEnableKeyPressed = False
    LastScreenCaptureCheck = 0

    SteeringOffset = 0
    SteeringSmoothness = 3
    SteeringSensitivity = 0.5
    SteeringMaximum = 1

    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()

    ScreenCapture.Initialize()
    ShowImage.Initialize(Name="NavigationDetectionV4", TitleBarColor=(0, 0, 0))


def GetTextSize(text="NONE", text_width=100, max_text_height=100):
    fontscale = 1
    textsize, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, 1)
    width_current_text, height_current_text = textsize
    max_count_current_text = 3
    while width_current_text != text_width or height_current_text > max_text_height:
        fontscale *= min(text_width / textsize[0], max_text_height / textsize[1])
        textsize, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, 1)
        max_count_current_text -= 1
        if max_count_current_text <= 0:
            break
    thickness = round(fontscale * 2)
    if thickness <= 0:
        thickness = 1
    return text, fontscale, thickness, textsize[0], textsize[1]


def Run(Data):
    CurrentTime = time.time()

    global Enabled
    global EnableKey
    global EnableKeyPressed
    global LastEnableKeyPressed
    global LastScreenCaptureCheck

    global SDKController
    global TruckSimAPI

    APIDATA = TruckSimAPI.update()
    Frame = ScreenCapture.Capture(ImageType="cropped")

    if type(Frame) == type(None): return

    FrameWidth = Frame.shape[1]
    FrameHeight = Frame.shape[0]
    if FrameWidth <= 0 or FrameHeight <= 0:
        return

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

    EnableKeyPressed = keyboard.is_pressed(EnableKey)
    if EnableKeyPressed == False and LastEnableKeyPressed == True:
        Enabled = not Enabled
    LastEnableKeyPressed = EnableKeyPressed


    LowerRed = np.array([0, 0, 160])
    UpperRed = np.array([110, 110, 255])
    Mask = cv2.inRange(Frame, LowerRed, UpperRed)
    Frame = cv2.bitwise_and(Frame, Frame, mask=Mask)
    Frame = cv2.cvtColor(Frame, cv2.COLOR_BGR2GRAY)


    LaneEdges = []

    for _ in range(5):

        Y = round(FrameHeight * 0.4 - _ * 3)

        LeftEdge = [0, Y]
        RightEdge = [FrameWidth - 1, Y]

        for i in range(2):
            DetectedLane = False
            DetectingLane = False
            for j in range(int(FrameWidth / 2)):
                if i == 0:
                    X = int(FrameWidth / 2) - j
                else:
                    X = int(FrameWidth / 2) + j

                if (Frame[Y][X] > 0) if not DetectingLane else (Frame[Y][X] == 0):
                    DetectedLane = True
                    DetectingLane = not DetectingLane
                    if DetectingLane == False:
                        if i == 0:
                            LeftEdge = [X, Y]
                        else:
                            RightEdge = [X, Y]
                        break
            DetectingLane = True
            if DetectedLane == False:
                for j in range(int(FrameWidth / 2)):
                    if i == 0:
                        X = int(FrameWidth / 2) + j
                    else:
                        X = int(FrameWidth / 2) - j

                    if (Frame[Y][X] > 0) if DetectingLane else (Frame[Y][X] == 0):
                        DetectedLane = True
                        DetectingLane = not DetectingLane
                        if DetectingLane == False:
                            if i == 0:
                                LeftEdge = [X, Y]
                            else:
                                RightEdge = [X, Y]
                            break

        LaneEdges.append((LeftEdge, RightEdge))

    ValidLanes = [True] * len(LaneEdges)

    for i in range(len(LaneEdges)):
        AvgLeftX = 0
        AvgRightX = 0
        for j in range(len(LaneEdges)):
            if i != j:
                AvgLeftX += LaneEdges[j][0][0]
                AvgRightX += LaneEdges[j][1][0]

        AvgLeftX /= len(LaneEdges) - 1
        AvgRightX /= len(LaneEdges) - 1

        if abs(LaneEdges[i][0][0] - AvgLeftX) > (abs(AvgRightX - AvgLeftX) / 3) or abs(AvgRightX - LaneEdges[i][1][0]) > (abs(AvgRightX - AvgLeftX) / 4):
            ValidLanes[i] = False

    Frame = cv2.cvtColor(Frame, cv2.COLOR_GRAY2BGR)

    for i, (LeftEdge, RightEdge) in enumerate(LaneEdges):
        cv2.line(Frame, LeftEdge, RightEdge, (0, 255, 0) if ValidLanes[i] else (0, 0, 255), 2)

    if len([ValidLane for ValidLane in ValidLanes if ValidLane == True]) > 0:
        LeftEdge = sum([LeftEdge[0] for i, (LeftEdge, RightEdge) in enumerate(LaneEdges) if ValidLanes[i] == True]) / len([ValidLane for ValidLane in ValidLanes if ValidLane == True]), sum([LeftEdge[1] for i, (LeftEdge, RightEdge) in enumerate(LaneEdges) if ValidLanes[i] == True]) / len([ValidLane for ValidLane in ValidLanes if ValidLane == True])
        RightEdge = sum([RightEdge[0] for i, (LeftEdge, RightEdge) in enumerate(LaneEdges) if ValidLanes[i] == True]) / len([ValidLane for ValidLane in ValidLanes if ValidLane == True]), sum([RightEdge[1] for i, (LeftEdge, RightEdge) in enumerate(LaneEdges) if ValidLanes[i] == True]) / len([ValidLane for ValidLane in ValidLanes if ValidLane == True])
    else:
        LeftEdge = 0, 0
        RightEdge = FrameWidth - 1, 0

    Steering = ((LeftEdge[0] + RightEdge[0]) / 2 - (FrameWidth - 1) / 2) / (FrameWidth - 1)

    Steering *= 5

    SDKController.steering = float(Steering)

    Text, Fontscale, Thickness, _, TextHeight = GetTextSize(text="Enabled" if Enabled else "Disabled", text_width=FrameWidth/1.1, max_text_height=FrameHeight/11)
    cv2.putText(Frame, Text, (5, 5 + TextHeight), cv2.FONT_HERSHEY_SIMPLEX, Fontscale, (0, 255, 0) if Enabled else (0, 0, 255), Thickness, cv2.LINE_AA)

    ShowImage.Show("NavigationDetectionV4", Frame)