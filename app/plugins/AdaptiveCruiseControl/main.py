from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from modules.SDKController.main import SCSController
import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage
from modules.Camera.main import SCSCamera
import src.settings as settings
import src.plugins as plugins
import src.pytorch as pytorch
import numpy as np
import keyboard
import math
import time
import cv2


PURPLE = "\033[95m"
NORMAL = "\033[0m"


def Initialize():
    global Enabled
    global EnableKey
    global EnableKeyPressed
    global LastEnableKeyPressed
    global SteeringHistory

    global Identifier

    global SDKController
    global TruckSimAPI
    global Camera
    global FOV

    Enabled = True
    EnableKey = settings.Get("Controls", "Steering", "n")
    EnableKeyPressed = False
    LastEnableKeyPressed = False
    SteeringHistory = []

    Identifier = pytorch.Initialize(Owner="OleFranz", Model="MLVSS", Folder="models/mapping")
    pytorch.Load(Identifier)

    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()
    Camera = SCSCamera()

    FOV = Camera.update().fov
    if FOV == 0:
        FOV = 80

    ScreenCapture.Initialize()
    ShowImage.Initialize(Name="AdaptiveCruiseControl", TitleBarColor=(0, 0, 0))


def GenerateImage(Image):
    with pytorch.torch.no_grad():
        Prediction = pytorch.MODELS[Identifier]["Model"](Image.unsqueeze(0).to(pytorch.MODELS[Identifier]["Device"]))
    Image = Image.permute(1, 2, 0).numpy()
    Image = cv2.cvtColor(Image, cv2.COLOR_BGR2BGRA)
    Prediction = Prediction.squeeze(0).cpu()
    for PredictionImage in Prediction:
        PredictionImage = cv2.resize(cv2.cvtColor(PredictionImage.numpy(), cv2.COLOR_GRAY2BGRA), (Image.shape[1], Image.shape[0]))
        PredictionImage[:, :, 2] = 0
        Image = cv2.addWeighted(Image, 1, PredictionImage, 0.5, 0)
    Image = cv2.cvtColor(Image, cv2.COLOR_BGRA2BGR)
    return Image


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

    FovRad = math.radians(FOV)

    WindowDistance = ((ScreenCapture.MonitorY2 - ScreenCapture.MonitorY1) * (4 / 3) / 2) / math.tan(FovRad / 2)

    ScreenX = (FinalX / FinalZ) * WindowDistance + (ScreenCapture.MonitorX2 - ScreenCapture.MonitorX1) / 2
    ScreenY = (FinalY / FinalZ) * WindowDistance + (ScreenCapture.MonitorY2 - ScreenCapture.MonitorY1) / 2

    ScreenX = (ScreenCapture.MonitorX2 - ScreenCapture.MonitorX1) - ScreenX

    Distance = math.sqrt((RelativeX ** 2) + (RelativeY ** 2) + (RelativeZ ** 2))

    return ScreenX, ScreenY, Distance


def CalculateRadiusFrontWheel(SteeringAngle, Distance):
    SteeringAngle = math.radians(SteeringAngle)
    if SteeringAngle != 0:
        return Distance / math.sin(SteeringAngle)
    else:
        return float("inf")


def CalculateRadiusBackWheel(SteeringAngle, Distance):
    SteeringAngle = math.radians(SteeringAngle)
    if SteeringAngle != 0:
        return Distance / math.tan(SteeringAngle)
    else:
        return float("inf")


def Run(data):
    CurrentTime = time.time()

    global Enabled
    global EnableKey
    global EnableKeyPressed
    global LastEnableKeyPressed

    global SDKController
    global TruckSimAPI

    global HeadRotationDegreesX
    global HeadRotationDegreesY
    global HeadRotationDegreesZ
    global HeadX
    global HeadY
    global HeadZ

    APIDATA = TruckSimAPI.update()

    if pytorch.Loaded(Identifier) == False: time.sleep(0.1); return

    ScreenCapture.TrackWindow(Name="Truck Simulator", Blacklist=["Discord"])

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


    CameraData = Camera.update()
    if CameraData is not None:
        FOV = CameraData.fov
        Angles = CameraData.rotation.euler()
        HeadX = CameraData.position.x + CameraData.cx * 512
        HeadY = CameraData.position.y
        HeadZ = CameraData.position.z + CameraData.cz * 512
        HeadRotationDegreesX = Angles[1]
        HeadRotationDegreesY = Angles[0]
        HeadRotationDegreesZ = Angles[2]


    TruckWheelPointsX = [Point for Point in APIDATA["configVector"]["truckWheelPositionX"] if Point != 0]
    TruckWheelPointsY = [Point for Point in APIDATA["configVector"]["truckWheelPositionY"] if Point != 0]
    TruckWheelPointsZ = [Point for Point in APIDATA["configVector"]["truckWheelPositionZ"] if Point != 0]

    WheelAngles = [Angle for Angle in APIDATA["truckFloat"]["truck_wheelSteering"] if Angle != 0]

    WheelCoordinates = []
    for i in range(len(TruckWheelPointsX)):
        PointX = TruckX + TruckWheelPointsX[i] * math.cos(TruckRotationRadiansX) - TruckWheelPointsZ[i] * math.sin(TruckRotationRadiansX)
        PointY = TruckY + TruckWheelPointsY[i]
        PointZ = TruckZ + TruckWheelPointsZ[i] * math.cos(TruckRotationRadiansX) + TruckWheelPointsX[i] * math.sin(TruckRotationRadiansX)
        WheelCoordinates.append((PointX, PointY, PointZ))


    if len(WheelCoordinates) >= 4 and len(WheelAngles) >= 2:
        FrontLeftWheel = WheelCoordinates[0]
        FrontRightWheel = WheelCoordinates[1]

        BackLeftWheels = []
        BackRightWheels = []

        for i in range(len(WheelCoordinates)):
            if len(WheelAngles) > i:
                continue

            if i % 2 == 0:
                BackLeftWheels.append(WheelCoordinates[i])
            else:
                BackRightWheels.append(WheelCoordinates[i])

        BackLeftWheel = (0, 0, 0)
        BackRightWheel = (0, 0, 0)

        for Wheel in BackLeftWheels:
            BackLeftWheel = BackLeftWheel[0] + Wheel[0], BackLeftWheel[1] + Wheel[1], BackLeftWheel[2] + Wheel[2]

        for Wheel in BackRightWheels:
            BackRightWheel = BackRightWheel[0] + Wheel[0], BackRightWheel[1] + Wheel[1], BackRightWheel[2] + Wheel[2]

        BackLeftWheel = BackLeftWheel[0] / len(BackLeftWheels), BackLeftWheel[1] / len(BackLeftWheels), BackLeftWheel[2] / len(BackLeftWheels)
        BackRightWheel = BackRightWheel[0] / len(BackRightWheels), BackRightWheel[1] / len(BackRightWheels), BackRightWheel[2] / len(BackRightWheels)

        FrontLeftSteerAngle = WheelAngles[0] * 360
        FrontRightSteerAngle = WheelAngles[1] * 360

        DistanceLeft = math.sqrt((FrontLeftWheel[0] - BackLeftWheel[0]) ** 2 + (FrontLeftWheel[2] - BackLeftWheel[2]) ** 2)
        DistanceRight = math.sqrt((FrontRightWheel[0] - BackRightWheel[0]) ** 2 + (FrontRightWheel[2] - BackRightWheel[2]) ** 2)

        LeftFrontWheelRadius = CalculateRadiusFrontWheel(FrontLeftSteerAngle, DistanceLeft)
        LeftBackWheelRadius = CalculateRadiusBackWheel(FrontLeftSteerAngle, DistanceLeft)
        RightFrontWheelRadius = CalculateRadiusFrontWheel(FrontRightSteerAngle, DistanceRight)
        RightBackWheelRadius = CalculateRadiusBackWheel(FrontRightSteerAngle, DistanceRight)

        LeftCenterX = BackLeftWheel[0] - LeftBackWheelRadius * math.cos(TruckRotationRadiansX)
        LeftCenterZ = BackLeftWheel[2] - LeftBackWheelRadius * math.sin(TruckRotationRadiansX)
        RightCenterX = BackRightWheel[0] - RightBackWheelRadius * math.cos(TruckRotationRadiansX)
        RightCenterZ = BackRightWheel[2] - RightBackWheelRadius * math.sin(TruckRotationRadiansX)

        LeftPoints = []
        RightPoints = []
        for i in range(2):
            if i == 0:
                R = LeftFrontWheelRadius - 1
                CenterX = LeftCenterX
                CenterZ = LeftCenterZ
                Offset = math.degrees(math.atan(DistanceLeft / R))
            else:
                R = RightFrontWheelRadius + 1
                CenterX = RightCenterX
                CenterZ = RightCenterZ
                Offset = math.degrees(math.atan(DistanceRight / R))
            for j in range(30):
                Angle = j * (1 / -R) * 60 - TruckRotationDegreesX - Offset
                Angle = math.radians(Angle)
                X = CenterX + R * math.cos(Angle)
                Z = CenterZ + R * math.sin(Angle)

                X, Y, D = ConvertToScreenCoordinate(X=X, Y=TruckY, Z=Z)
                if X != None and Y != None:
                    if i == 0:
                        LeftPoints.append([X, Y])
                    else:
                        RightPoints.append([X, Y])

        AllPoints = LeftPoints + RightPoints[::-1]
        if len(AllPoints) >= 4:
            cv2.fillPoly(Frame, np.array([AllPoints], dtype=np.int32), (255, 255, 255))


    #Image = np.array(Frame, dtype=np.float32)
    #if pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'Grayscale' or pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'Binarize':
    #    Image = cv2.cvtColor(Image, cv2.COLOR_RGB2GRAY)
    #if pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'RG':
    #    Image = np.stack((Image[:, :, 0], Image[:, :, 1]), axis=2)
    #elif pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'GB':
    #    Image = np.stack((Image[:, :, 1], Image[:, :, 2]), axis=2)
    #elif pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'RB':
    #    Image = np.stack((Image[:, :, 0], Image[:, :, 2]), axis=2)
    #elif pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'R':
    #    Image = Image[:, :, 0]
    #    Image = np.expand_dims(Image, axis=2)
    #elif pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'G':
    #    Image = Image[:, :, 1]
    #    Image = np.expand_dims(Image, axis=2)
    #elif pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'B':
    #    Image = Image[:, :, 2]
    #    Image = np.expand_dims(Image, axis=2)
    #Image = cv2.resize(Image, (pytorch.MODELS[Identifier]["IMG_WIDTH"], pytorch.MODELS[Identifier]["IMG_HEIGHT"]))
    #Image = Image / 255.0
    #if pytorch.MODELS[Identifier]["IMG_CHANNELS"] == 'Binarize':
    #    Image = cv2.threshold(Image, 0.5, 1.0, cv2.THRESH_BINARY)[1]
    #Image = pytorch.transforms.ToTensor()(Image)


    EnableKeyPressed = keyboard.is_pressed(EnableKey)
    if EnableKeyPressed == False and LastEnableKeyPressed == True:
        Enabled = not Enabled
    LastEnableKeyPressed = EnableKeyPressed

    #if Enabled == True:
    #    if pytorch.MODELS[Identifier]["ModelLoaded"] == True:
    #        Frame = GenerateImage(Image)

    ShowImage.Show("AdaptiveCruiseControl", Frame)