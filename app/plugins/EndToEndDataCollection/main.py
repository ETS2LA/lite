from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from modules.SDKController.main import SCSController
import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage
from torchvision import transforms
import src.variables as variables
import src.plugins as plugins
import numpy as np
import keyboard
import torch
import math
import time
import cv2
import os


def Initialize():
    global SDKController
    global TruckSimAPI

    global LastScreenCaptureCheck
    LastScreenCaptureCheck = 0

    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()

    ScreenCapture.Initialize()
    ShowImage.Initialize("EndToEndDataCollection", (0, 0, 0))


    global MODE
    MODE = ["Use", "Collect"][0]

    global ENABLED, KEY
    ENABLED = False
    KEY = "y"

    global LastEnabledPressed, LastCapture
    LastEnabledPressed = False
    LastCapture = 0


    global METADATA
    global DEVICE
    global MODEL

    global IMG_WIDTH
    global IMG_HEIGHT
    global IMG_CHANNELS
    global MODEL_OUTPUTS

    METADATA = {"data": []}
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    MODEL = None
    for File in os.listdir(f"{variables.PATH}cache/Use/"):
        if File.endswith(".pt"):
            MODEL = torch.jit.load(f"{variables.PATH}cache/Use/{File}", _extra_files=METADATA, map_location=DEVICE)
            break
    if MODEL == None:
        plugins.AddToQueue({"MANAGEPLUGINS": ["RouteAdvisorClassification", "Stop"]})
        return

    METADATA = eval(METADATA["data"])

    for item in METADATA:
        item = str(item)
        if "image_width" in item:
            IMG_WIDTH = int(item.split("#")[1])
        if "image_height" in item:
            IMG_HEIGHT = int(item.split("#")[1])
        if "image_channels" in item:
            IMG_CHANNELS = str(item.split("#")[1])
        if "outputs" in item:
            MODEL_OUTPUTS = int(item.split("#")[1])


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

    global HeadRotationDegreesX
    global HeadRotationDegreesY
    global HeadRotationDegreesZ
    global HeadX
    global HeadY
    global HeadZ

    global ENABLED, LastEnabledPressed, LastCapture

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


    OffsetX = 2
    OffsetY = 0.1
    OffsetZ = 1.5

    PointX = HeadX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = HeadY + OffsetY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = HeadZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        TopLeft = X, Y
        Points.append((PointX, PointY, PointZ))


    OffsetX = 2
    OffsetY = 0.1
    OffsetZ = -1.5

    PointX = HeadX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = HeadY + OffsetY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = HeadZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        TopRight = X, Y
        Points.append((PointX, PointY, PointZ))


    OffsetX = 2
    OffsetY = -0.5
    OffsetZ = 1.5

    PointX = HeadX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = HeadY + OffsetY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = HeadZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        BottomLeft = X, Y
        Points.append((PointX, PointY, PointZ))


    OffsetX = 2
    OffsetY = -0.5
    OffsetZ = -1.5

    PointX = HeadX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = HeadY + OffsetY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = HeadZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        BottomRight = X, Y
        Points.append((PointX, PointY, PointZ))


    if AllCoordinatesValid:
        CroppedWidth = round(max(TopRight[0] - TopLeft[0], BottomRight[0] - BottomLeft[0]))
        CroppedHeight = round(max(BottomLeft[1] - TopLeft[1], BottomRight[1] - TopRight[1]))
        SourcePoints = np.float32([TopLeft, TopRight, BottomLeft, BottomRight])
        DestinationPoints = np.float32([[0, 0], [CroppedWidth, 0], [0, CroppedHeight], [CroppedWidth, CroppedHeight]])
        Matrix = cv2.getPerspectiveTransform(SourcePoints, DestinationPoints)
        Frame = cv2.warpPerspective(Frame, Matrix, (CroppedWidth, CroppedHeight))


    if MODE == "Collect":
        INGAME = APIDATA["pause"] == False and ScreenCapture.IsForegroundWindow(Name="Truck Simulator", Blacklist=["Discord"]) == True
        if LastCapture + 0.5 <= time.time() and ENABLED and INGAME:
            LastCapture = time.time()
            Steering = APIDATA["truckFloat"]["userSteer"]
            Name = str(round(time.time(), 2)).replace(".", "_")
            Folder = f"{variables.PATH}cache/DataCollection/"
            if not os.path.exists(Folder):
                os.makedirs(Folder)
            with open(Folder + Name + ".txt", "w") as File:
                File.write(str(Steering))
                File.close()
            cv2.imwrite(Folder + Name + ".png", Frame)

    elif MODE == "Use":
            
        Image = np.array(Frame, dtype=np.float32)
        if IMG_CHANNELS == 'Grayscale' or IMG_CHANNELS == 'Binarize':
            Image = cv2.cvtColor(Image, cv2.COLOR_RGB2GRAY)
        if IMG_CHANNELS == 'RG':
            Image = np.stack((Image[:, :, 0], Image[:, :, 1]), axis=2)
        elif IMG_CHANNELS == 'GB':
            Image = np.stack((Image[:, :, 1], Image[:, :, 2]), axis=2)
        elif IMG_CHANNELS == 'RB':
            Image = np.stack((Image[:, :, 0], Image[:, :, 2]), axis=2)
        elif IMG_CHANNELS == 'R':
            Image = Image[:, :, 0]
            Image = np.expand_dims(Image, axis=2)
        elif IMG_CHANNELS == 'G':
            Image = Image[:, :, 1]
            Image = np.expand_dims(Image, axis=2)
        elif IMG_CHANNELS == 'B':
            Image = Image[:, :, 2]
            Image = np.expand_dims(Image, axis=2)
        Image = cv2.resize(Image, (IMG_WIDTH, IMG_HEIGHT))
        Image = Image / 255.0
        if IMG_CHANNELS == 'Binarize':
            Image = cv2.threshold(Image, 0.5, 1.0, cv2.THRESH_BINARY)[1]
        Image = transforms.ToTensor()(Image).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            Output = float(np.array(MODEL(Image)[0].tolist()))
        SDKController.steering = Output / -20


    if ENABLED:
        cv2.rectangle(Frame, (0, 0), (Frame.shape[1] - 1, Frame.shape[0] - 1), (0, 255, 0), 5)
    else:
        cv2.rectangle(Frame, (0, 0), (Frame.shape[1] - 1, Frame.shape[0] - 1), (0, 0, 255), 5)


    EnabledPressed = keyboard.is_pressed(KEY)
    if LastEnabledPressed == False and EnabledPressed == True:
        ENABLED = not ENABLED
    LastEnabledPressed = EnabledPressed


    ShowImage.Show("EndToEndDataCollection", Frame)