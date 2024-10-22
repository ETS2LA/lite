from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from modules.SDKController.main import SCSController
import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage
import src.variables as variables
import numpy as np
import time
import math
import cv2

if variables.OS == "nt":
    import win32gui, win32con
    from ctypes import windll, byref, sizeof, c_int


def Initialize():
    global SDKController
    global TruckSimAPI

    global LastScreenCaptureCheck
    global LastScale
    global Images
    global RESOLUTION
    global FRAME

    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()

    ScreenCapture.Initialize()
    ShowImage.Initialize(Name="VisionMap", TitleBarColor=(0, 0, 0))

    LastScreenCaptureCheck = 0
    LastScale = None
    Images = []
    RESOLUTION = 700
    FRAME = np.zeros((RESOLUTION, RESOLUTION, 3), np.uint8)


def ConvertToScreenCoordinate(X: float, Y: float, Z: float):
    HeadYaw = HeadRotationDegreesX
    HeadPitch = HeadRotationDegreesY
    HeadRoll = HeadRotationDegreesZ

    RelativeX = X - HeadX
    RelativeY = Y - HeadY
    RelativeZ = Z - HeadZ

    CosYaw = math.cos(math.radians(-HeadYaw))
    SinYaw = math.sin(math.radians(-HeadYaw))
    NewX = RelativeX * CosYaw + RelativeZ * SinYaw
    NewZ = RelativeZ * CosYaw - RelativeX * SinYaw

    CosPitch = math.cos(math.radians(-HeadPitch))
    SinPitch = math.sin(math.radians(-HeadPitch))
    NewY = RelativeY * CosPitch - NewZ * SinPitch
    FinalZ = NewZ * CosPitch + RelativeY * SinPitch

    CosRoll = math.cos(math.radians(HeadRoll))
    SinRoll = math.sin(math.radians(HeadRoll))
    FinalX = NewX * CosRoll - NewY * SinRoll
    FinalY = NewY * CosRoll + NewX * SinRoll

    if FinalZ >= 0:
        return None, None, None

    FovRad = math.radians(variables.FOV)
    
    WindowDistance = ((ScreenCapture.MonitorY2 - ScreenCapture.MonitorY1) * (4 / 3) / 2) / math.tan(FovRad / 2)

    ScreenX = (FinalX / FinalZ) * WindowDistance + (ScreenCapture.MonitorX2 - ScreenCapture.MonitorX1) / 2
    ScreenY = (FinalY / FinalZ) * WindowDistance + (ScreenCapture.MonitorY2 - ScreenCapture.MonitorY1) / 2

    ScreenX = (ScreenCapture.MonitorX2 - ScreenCapture.MonitorX1) - ScreenX

    Distance = math.sqrt((RelativeX ** 2) + (RelativeY ** 2) + (RelativeZ ** 2))

    return ScreenX, ScreenY, Distance


def Run(data):
    CurrentTime = time.time()

    global LastScreenCaptureCheck
    global LastScale
    global FRAME

    global HeadRotationDegreesX
    global HeadRotationDegreesY
    global HeadRotationDegreesZ
    global HeadX
    global HeadY
    global HeadZ

    APIDATA = TruckSimAPI.update()

    if LastScreenCaptureCheck + 0.5 < time.time():
        X1, Y1, X2, Y2 = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
        ScreenX, ScreenY, _, _ = ScreenCapture.GetScreenDimensions(ScreenCapture.GetScreenIndex((X1 + X2) / 2, (Y1 + Y2) / 2))
        if ScreenCapture.MonitorX1 != X1 - ScreenX or ScreenCapture.MonitorY1 != Y1 - ScreenY or ScreenCapture.MonitorX2 != X2 - ScreenX or ScreenCapture.MonitorY2 != Y2 - ScreenY:
            ScreenIndex = ScreenCapture.GetScreenIndex((X1 + X2) / 2, (Y1 + Y2) / 2)
            if ScreenCapture.Display != ScreenIndex - 1:
                if ScreenCapture.CaptureLibrary == "WindowsCapture":
                    ScreenCapture.StopWindowsCapture = True
                    while ScreenCapture.StopWindowsCapture == True:
                        time.sleep(0.01)
                ScreenCapture.Initialize()
            ScreenCapture.MonitorX1, ScreenCapture.MonitorY1, ScreenCapture.MonitorX2, ScreenCapture.MonitorY2 = ScreenCapture.ValidateCaptureArea(ScreenIndex, X1 - ScreenX, Y1 - ScreenY, X2 - ScreenX, Y2 - ScreenY)
        LastScreenCaptureCheck = CurrentTime

    Frame = ScreenCapture.Capture(ImageType="cropped")
    if type(Frame) == type(None) or Frame.shape[0] <= 0 or Frame.shape[1] <= 0:
        return


    TruckX = APIDATA["truckPlacement"]["coordinateX"]
    TruckY = APIDATA["truckPlacement"]["coordinateY"]
    TruckZ = APIDATA["truckPlacement"]["coordinateZ"]
    TruckRotationX = APIDATA["truckPlacement"]["rotationX"]
    TruckRotationY = APIDATA["truckPlacement"]["rotationY"]
    TruckRotationZ = APIDATA["truckPlacement"]["rotationZ"]

    CabinOffsetX = APIDATA["headPlacement"]["cabinOffsetX"] + APIDATA["configVector"]["cabinPositionX"]
    CabinOffsetY = APIDATA["headPlacement"]["cabinOffsetY"] + APIDATA["configVector"]["cabinPositionY"]
    CabinOffsetZ = APIDATA["headPlacement"]["cabinOffsetZ"] + APIDATA["configVector"]["cabinPositionZ"]
    CabinOffsetRotationX = APIDATA["headPlacement"]["cabinOffsetrotationX"]
    CabinOffsetRotationY = APIDATA["headPlacement"]["cabinOffsetrotationY"]
    CabinOffsetRotationZ = APIDATA["headPlacement"]["cabinOffsetrotationZ"]

    HeadOffsetX = APIDATA["headPlacement"]["headOffsetX"] + APIDATA["configVector"]["headPositionX"] + CabinOffsetX
    HeadOffsetY = APIDATA["headPlacement"]["headOffsetY"] + APIDATA["configVector"]["headPositionY"] + CabinOffsetY
    HeadOffsetZ = APIDATA["headPlacement"]["headOffsetZ"] + APIDATA["configVector"]["headPositionZ"] + CabinOffsetZ
    HeadOffsetRotationX = APIDATA["headPlacement"]["headOffsetrotationX"]
    HeadOffsetRotationY = APIDATA["headPlacement"]["headOffsetrotationY"]
    HeadOffsetRotationZ = APIDATA["headPlacement"]["headOffsetrotationZ"]

    TruckRotationDegreesX = TruckRotationX * 360
    TruckRotationRadiansX = -math.radians(TruckRotationDegreesX)

    HeadRotationDegreesX = (TruckRotationX + CabinOffsetRotationX + HeadOffsetRotationX) * 360
    while HeadRotationDegreesX > 360:
        HeadRotationDegreesX = HeadRotationDegreesX - 360

    HeadRotationDegreesY = (TruckRotationY + CabinOffsetRotationY + HeadOffsetRotationY) * 360

    HeadRotationDegreesZ = (TruckRotationZ + CabinOffsetRotationZ + HeadOffsetRotationZ) * 360

    PointX = HeadOffsetX
    PointY = HeadOffsetY
    PointZ = HeadOffsetZ
    HeadX = PointX * math.cos(TruckRotationRadiansX) - PointZ * math.sin(TruckRotationRadiansX) + TruckX
    HeadY = PointY + TruckY
    HeadZ = PointX * math.sin(TruckRotationRadiansX) + PointZ * math.cos(TruckRotationRadiansX) + TruckZ


    TruckWheelPointsX = [Point for Point in APIDATA["configVector"]["truckWheelPositionX"] if Point != 0]
    TruckWheelPointsY = [Point for Point in APIDATA["configVector"]["truckWheelPositionY"] if Point != 0]
    TruckWheelPointsZ = [Point for Point in APIDATA["configVector"]["truckWheelPositionZ"] if Point != 0]

    WheelAngles = [Angle for Angle in APIDATA["truckFloat"]["truck_wheelSteering"] if Angle != 0]
    while int(APIDATA["configUI"]["truckWheelCount"]) > len(WheelAngles):
        WheelAngles.append(0)

    for i in range(len(TruckWheelPointsX)):
        PointX = TruckX + TruckWheelPointsX[i] * math.cos(TruckRotationRadiansX) - TruckWheelPointsZ[i] * math.sin(TruckRotationRadiansX)
        PointY = TruckY + TruckWheelPointsY[i]
        PointZ = TruckZ + TruckWheelPointsZ[i] * math.cos(TruckRotationRadiansX) + TruckWheelPointsX[i] * math.sin(TruckRotationRadiansX)
        X, Y, D = ConvertToScreenCoordinate(X=PointX, Y=PointY, Z=PointZ)


    AllCoordinatesValid = True
    Points = []


    OffsetX = 50
    OffsetZ = 14

    PointX = TruckX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = TruckY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = TruckZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        TopLeft = X, Y
        Points.append((PointX, PointZ))


    OffsetX = 50
    OffsetZ = -14

    PointX = TruckX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = TruckY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = TruckZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        TopRight = X, Y
        Points.append((PointX, PointZ))


    OffsetX = 13
    OffsetZ = 4

    PointX = TruckX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = TruckY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = TruckZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        BottomLeft = X, Y
        Points.append((PointX, PointZ))


    OffsetX = 13
    OffsetZ = -4

    PointX = TruckX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = TruckY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = TruckZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        BottomRight = X, Y
        Points.append((PointX, PointZ))


    if AllCoordinatesValid:
        CroppedWidth = round(max(TopRight[0] - TopLeft[0], BottomRight[0] - BottomLeft[0]))
        CroppedHeight = round(max(BottomLeft[1] - TopLeft[1], BottomRight[1] - TopRight[1]))
        SourcePoints = np.float32([TopLeft, TopRight, BottomLeft, BottomRight])
        DestinationPoints = np.float32([[0, 0], [CroppedWidth, 0], [0, CroppedHeight], [CroppedWidth, CroppedHeight]])
        Matrix = cv2.getPerspectiveTransform(SourcePoints, DestinationPoints)
        Frame = cv2.warpPerspective(Frame, Matrix, (CroppedWidth, CroppedHeight))

        Images.append((Frame, Points, False))

    MinX = float('inf')
    MaxX = float('-inf')
    MinZ = float('inf')
    MaxZ = float('-inf')

    for Image, Points, _ in Images:
        for PointX, PointZ in Points:
            MinX = min(MinX, PointX)
            MaxX = max(MaxX, PointX)
            MinZ = min(MinZ, PointZ)
            MaxZ = max(MaxZ, PointZ)


    ScaleX = RESOLUTION / (MaxX - MinX)
    ScaleZ = RESOLUTION / (MaxZ - MinZ)
    Scale = min(ScaleX, ScaleZ)
    if Scale != LastScale:
        for i, (Image, Points, Rendered) in enumerate(Images):
            Images[i] = (Image, Points, False)
        FRAME = np.zeros((RESOLUTION, RESOLUTION, 3), np.uint8)
    LastScale = Scale

    for i, (Image, Points, Rendered) in enumerate(Images):
        if Rendered == True:
            continue
        Images[i] = (Image, Points, True)
        OnFrameX1 = (Points[0][0] - MinX) * Scale
        OnFrameY1 = (Points[0][1] - MinZ) * Scale
        OnFrameX2 = (Points[2][0] - MinX) * Scale
        OnFrameY2 = (Points[2][1] - MinZ) * Scale
        onframe_x3 = (Points[3][0] - MinX) * Scale
        onframe_y3 = (Points[3][1] - MinZ) * Scale
        onframe_x4 = (Points[1][0] - MinX) * Scale
        onframe_y4 = (Points[1][1] - MinZ) * Scale

        SourcePoints = np.float32([[0, 0], [Image.shape[1], 0], [0, Image.shape[0]], [Image.shape[1], Image.shape[0]]])
        DestinationPoints = np.float32([[OnFrameX1, OnFrameY1], [onframe_x4, onframe_y4], [OnFrameX2, OnFrameY2], [onframe_x3, onframe_y3]])
        Matrix = cv2.getPerspectiveTransform(SourcePoints, DestinationPoints)
        warped_image = cv2.warpPerspective(Image, Matrix, (RESOLUTION, RESOLUTION), flags=cv2.INTER_NEAREST)
        Mask = cv2.inRange(warped_image, np.array([1, 1, 1]), np.array([255, 255, 255]))
        FRAME[Mask > 0] = warped_image[Mask > 0]

    Frame = FRAME.copy()
    time.sleep(0.05)

    X = TruckX
    Y = TruckZ
    OnFrameX = (X - MinX) * Scale
    OnFrameY = (Y - MinZ) * Scale
    cv2.circle(Frame, (int(OnFrameX), int(OnFrameY)), 5, (0, 0, 255), -1)

    ShowImage.Show(Name="VisionMap", Frame=Frame)