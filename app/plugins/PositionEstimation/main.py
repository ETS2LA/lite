from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage

import ctypes
import mouse
import numpy
import math
import time
import cv2


def Initialize():
    global LastScreenCaptureCheck
    global LastMousePresses
    global TruckSimAPI
    global EmptyFrame

    LastScreenCaptureCheck = 0
    LastMousePresses = False, False
    TruckSimAPI = SCSTelemetry()
    EmptyFrame = numpy.zeros((500, 500, 3), numpy.uint8)


    global A, Alpha, ADragStart, ADragEnd
    A = None, None
    Alpha = None
    ADragStart = None, None
    ADragEnd = None, None

    global B, Beta, BDragStart, BDragEnd
    B = None, None
    Beta = None
    BDragStart = None, None
    BDragEnd = None, None


    ShowImage.Initialize(Name="PositionEstimation", TitleBarColor=(0, 0, 0))
    ScreenCapture.Initialize()


def DegToRad(Angle):
    return math.radians(Angle / 2 - 180)


def RadToDeg(Angle):
    return math.degrees(Angle) * 2 + 180


def Run(Data):
    CurrentTime = time.time()

    global LastScreenCaptureCheck
    global LastMousePresses

    global A, Alpha, ADragStart, ADragEnd
    global B, Beta, BDragStart, BDragEnd

    #APIDATA = TruckSimAPI.update()

    #if LastScreenCaptureCheck + 0.5 < CurrentTime:
    #    WindowX1, WindowY1, WindowX2, WindowY2 = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
    #    if ScreenCapture.MonitorX1 != WindowX1 or ScreenCapture.MonitorY1 != WindowY1 or ScreenCapture.MonitorX2!= WindowX2 or ScreenCapture.MonitorY2 != WindowY2:
    #        ScreenIndex = ScreenCapture.GetScreenIndex((WindowX1 + WindowX2) / 2, (WindowY1 + WindowY2) / 2)
    #        if ScreenCapture.Display != ScreenIndex - 1:
    #            if ScreenCapture.CaptureLibrary == "WindowsCapture":
    #                ScreenCapture.StopWindowsCapture = True
    #                while ScreenCapture.StopWindowsCapture == True:
    #                    time.sleep(0.01)
    #            ScreenCapture.Initialize()
    #        ScreenCapture.MonitorX1, ScreenCapture.MonitorY1, ScreenCapture.MonitorX2, ScreenCapture.MonitorY2 = ScreenCapture.ValidateCaptureArea(ScreenIndex, WindowX1, WindowY1, WindowX2, WindowY2)
    #    LastScreenCaptureCheck = CurrentTime

    #Frame = ScreenCapture.Capture(ImageType="cropped")
    #if type(Frame) == type(None) or Frame.shape[0] <= 0 or Frame.shape[1] <= 0:
    #    return

    Frame = EmptyFrame.copy()

    #TruckX = APIDATA["truckPlacement"]["coordinateX"]
    #TruckY = APIDATA["truckPlacement"]["coordinateY"]
    #TruckZ = APIDATA["truckPlacement"]["coordinateZ"]
    #TruckRotationX = APIDATA["truckPlacement"]["rotationX"]
    #TruckRotationY = APIDATA["truckPlacement"]["rotationY"]
    #TruckRotationZ = 0

    #CabinOffsetX = APIDATA["headPlacement"]["cabinOffsetX"] + APIDATA["configVector"]["cabinPositionX"]
    #CabinOffsetY = APIDATA["headPlacement"]["cabinOffsetY"] + APIDATA["configVector"]["cabinPositionY"]
    #CabinOffsetZ = APIDATA["headPlacement"]["cabinOffsetZ"] + APIDATA["configVector"]["cabinPositionZ"]
    #CabinOffsetRotationX = APIDATA["headPlacement"]["cabinOffsetrotationX"]
    #CabinOffsetRotationY = APIDATA["headPlacement"]["cabinOffsetrotationY"]
    #CabinOffsetRotationZ = 0

    #HeadOffsetX = APIDATA["headPlacement"]["headOffsetX"] + APIDATA["configVector"]["headPositionX"] + CabinOffsetX
    #HeadOffsetY = APIDATA["headPlacement"]["headOffsetY"] + APIDATA["configVector"]["headPositionY"] + CabinOffsetY
    #HeadOffsetZ = APIDATA["headPlacement"]["headOffsetZ"] + APIDATA["configVector"]["headPositionZ"] + CabinOffsetZ
    #HeadOffsetRotationX = APIDATA["headPlacement"]["headOffsetrotationX"]
    #HeadOffsetRotationY = APIDATA["headPlacement"]["headOffsetrotationY"]
    #HeadOffsetRotationZ = 0

    #TruckRotationDegreesX = TruckRotationX * 360
    #TruckRotationRadiansX = -math.radians(TruckRotationDegreesX)

    #HeadRotationDegreesX = (TruckRotationX + CabinOffsetRotationX + HeadOffsetRotationX) * 360
    #while HeadRotationDegreesX > 360:
    #    HeadRotationDegreesX = HeadRotationDegreesX - 360

    #HeadRotationDegreesY = (TruckRotationY + CabinOffsetRotationY + HeadOffsetRotationY) * 360

    #HeadRotationDegreesZ = (TruckRotationZ + CabinOffsetRotationZ + HeadOffsetRotationZ) * 360

    #PointX = HeadOffsetX
    #PointY = HeadOffsetY
    #PointZ = HeadOffsetZ
    #HeadX = PointX * math.cos(TruckRotationRadiansX) - PointZ * math.sin(TruckRotationRadiansX) + TruckX
    #HeadY = PointY + TruckY
    #HeadZ = PointX * math.sin(TruckRotationRadiansX) + PointZ * math.cos(TruckRotationRadiansX) + TruckZ


    try:
        WindowX, WindowY, WindowWidth, WindowHeight = cv2.getWindowImageRect("PositionEstimation")

        MouseX, MouseY = mouse.get_position()
        MouseRelativeWindow = MouseX - WindowX, MouseY - WindowY
        if WindowWidth != 0 and WindowHeight != 0:
            MouseX = MouseRelativeWindow[0]/WindowWidth
            MouseY = MouseRelativeWindow[1]/WindowHeight
        else:
            MouseX = 0
            MouseY = 0
    except:
        ShowImage.Show(Name="PositionEstimation", Frame=Frame)
        return

    ForegroundWindow = ctypes.windll.user32.GetForegroundWindow() == ctypes.windll.user32.FindWindowW(None, "PositionEstimation")
    LeftClicked = ctypes.windll.user32.GetKeyState(0x01) & 0x8000 != 0 and ForegroundWindow and 0 < MouseX < 1 and 0 < MouseY < 1
    RightClicked = ctypes.windll.user32.GetKeyState(0x02) & 0x8000 != 0 and ForegroundWindow and 0 < MouseX < 1 and 0 < MouseY < 1
    LastLeftClicked = LastMousePresses[0]
    LastRightClicked = LastMousePresses[1]


    if LastLeftClicked == False and LeftClicked == True:
        A = MouseX * (Frame.shape[1] - 1), MouseY * (Frame.shape[0] - 1)
        ADragStart = A
        ADragEnd = None, None
    elif LastLeftClicked == True and LeftClicked == False:
        ADragEnd = MouseX * (Frame.shape[1] - 1), MouseY * (Frame.shape[0] - 1)
        if ADragEnd[0] != ADragStart[0]:
            Alpha = 180 - RadToDeg(math.atan((ADragEnd[1] - ADragStart[1]) / (ADragEnd[0] - ADragStart[0])))

    if LastRightClicked == False and RightClicked == True:
        B = MouseX * (Frame.shape[1] - 1), MouseY * (Frame.shape[0] - 1)
        BDragStart = B
        BDragEnd = None, None
    elif LastRightClicked == True and RightClicked == False:
        BDragEnd = MouseX * (Frame.shape[1] - 1), MouseY * (Frame.shape[0] - 1)
        if BDragEnd[0] != BDragStart[0]:
            Beta = RadToDeg(math.atan((BDragEnd[1] - BDragStart[1]) / (BDragEnd[0] - BDragStart[0])))


    if A[0] != None and A[1] != None and B[0] != None and B[1] != None:
        cv2.line(Frame, (round(A[0]), round(A[1])), (round(B[0]), round(B[1])), (100, 100, 100), round((Frame.shape[0] + Frame.shape[1]) / 400), cv2.LINE_AA)


    if ADragStart != (None, None) and ADragEnd != (None, None):
        cv2.line(Frame, (round(ADragStart[0]), round(ADragStart[1])), (round(ADragEnd[0]), round(ADragEnd[1])), (100, 100, 180), round((Frame.shape[0] + Frame.shape[1]) / 400), cv2.LINE_AA)

    if BDragStart != (None, None) and BDragEnd != (None, None):
        cv2.line(Frame, (round(BDragStart[0]), round(BDragStart[1])), (round(BDragEnd[0]), round(BDragEnd[1])), (100, 180, 100), round((Frame.shape[0] + Frame.shape[1]) / 400), cv2.LINE_AA)


    if A[0] != None and A[1] != None:
        cv2.circle(Frame, (round(A[0]), round(A[1])), round((Frame.shape[0] + Frame.shape[1]) / 200), (50, 50, 180), -1, cv2.LINE_AA)

    if B[0] != None and B[1] != None:
        cv2.circle(Frame, (round(B[0]), round(B[1])), round((Frame.shape[0] + Frame.shape[1]) / 200), (50, 180, 50), -1, cv2.LINE_AA)


    if A != (None, None) and Alpha != None and B != (None, None) and Beta != None:
        try:

            AngleAB = (90 - math.degrees(math.atan((B[1] - A[1]) / (B[0] - A[0])))) if (B[0] - A[0]) != 0 else 0
            print(AngleAB)
            TempAlpha = Alpha + AngleAB
            TempBeta = Beta + AngleAB

            b = (math.sqrt((A[0] - B[0]) ** 2 + (A[1] - B[1]) ** 2) / math.sin(DegToRad(180 - TempAlpha - TempBeta))) * math.sin(DegToRad(TempBeta))
            Cx = math.sin(DegToRad(180 - TempAlpha)) * b
            Cy =  math.cos(DegToRad(180 - TempAlpha)) * b

            C = A[0] - Cx, A[1] + Cy

            cv2.circle(Frame, (round(C[0]), round(C[1])), round((Frame.shape[0] + Frame.shape[1]) / 200), (180, 180, 180), -1, cv2.LINE_AA)

        except:
            pass

    LastMousePresses = LeftClicked, RightClicked

    ShowImage.Show(Name="PositionEstimation", Frame=Frame)

    TimeToSleep = 1/60 - (time.time() - CurrentTime)
    if TimeToSleep > 0:
        time.sleep(TimeToSleep)