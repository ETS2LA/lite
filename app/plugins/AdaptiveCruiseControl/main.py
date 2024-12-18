from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from modules.SDKController.main import SCSController
import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage
import src.variables as variables
import src.settings as settings
import numpy as np
import traceback
import time
import math
import cv2
import mss
import os

if variables.OS == "nt":
    import win32gui, win32con
    from ctypes import windll, byref, sizeof, c_int


#from torchvision import transforms
#import torch


def Initialize():
    global LastScreenCaptureCheck
    global SDKController
    global TruckSimAPI

    LastScreenCaptureCheck = 0
    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()

    ScreenCapture.Initialize()
    ShowImage.Initialize(Name="AdaptiveCruiseControl", TitleBarColor=(0, 0, 0))

    #global model
    #global device
    #device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    #print("Using device:", device)
    #for file in os.listdir(f"{variables.PATH}"):
    #    if file.endswith(".pt"):
    #        model = torch.jit.load(os.path.join(f"{variables.PATH}", file), device)
    #        model.eval()
    #        break


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
    global SDKController
    global TruckSimAPI

    global HeadRotationDegreesX
    global HeadRotationDegreesY
    global HeadRotationDegreesZ
    global HeadX
    global HeadY
    global HeadZ

    APIDATA = TruckSimAPI.update()

    if LastScreenCaptureCheck + 0.5 < CurrentTime:
        WindowX1, WindowY1, WindowX2, WindowY2 = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
        if ScreenCapture.MonitorX1 != WindowX1 or ScreenCapture.MonitorY1 != WindowY1 or ScreenCapture.MonitorX2!= WindowX2 or ScreenCapture.MonitorY2 != WindowY2:
            ScreenIndex = ScreenCapture.GetScreenIndex((WindowX1 + WindowX2) / 2, (WindowY1 + WindowY2) / 2)
            if ScreenCapture.Display != ScreenIndex - 1:
                if ScreenCapture.CaptureLibrary == "WindowsCapture":
                    ScreenCapture.StopWindowsCapture = True
                    while ScreenCapture.StopWindowsCapture == True:
                        time.sleep(0.01)
                ScreenCapture.Initialize()
            ScreenCapture.MonitorX1, ScreenCapture.MonitorY1, ScreenCapture.MonitorX2, ScreenCapture.MonitorY2 = ScreenCapture.ValidateCaptureArea(ScreenIndex, WindowX1, WindowY1, WindowX2, WindowY2)
        LastScreenCaptureCheck = CurrentTime

    Frame = ScreenCapture.Capture(ImageType="cropped")
    if type(Frame) == type(None) or Frame.shape[0] <= 0 or Frame.shape[1] <= 0:
        return


    TruckX = APIDATA["truckPlacement"]["coordinateX"]
    TruckY = APIDATA["truckPlacement"]["coordinateY"]
    TruckZ = APIDATA["truckPlacement"]["coordinateZ"]
    TruckRotationX = APIDATA["truckPlacement"]["rotationX"]
    TruckRotationY = APIDATA["truckPlacement"]["rotationY"]
    TruckRotationZ = 0

    CabinOffsetX = APIDATA["headPlacement"]["cabinOffsetX"] + APIDATA["configVector"]["cabinPositionX"]
    CabinOffsetY = APIDATA["headPlacement"]["cabinOffsetY"] + APIDATA["configVector"]["cabinPositionY"]
    CabinOffsetZ = APIDATA["headPlacement"]["cabinOffsetZ"] + APIDATA["configVector"]["cabinPositionZ"]
    CabinOffsetRotationX = APIDATA["headPlacement"]["cabinOffsetrotationX"]
    CabinOffsetRotationY = APIDATA["headPlacement"]["cabinOffsetrotationY"]
    CabinOffsetRotationZ = 0

    HeadOffsetX = APIDATA["headPlacement"]["headOffsetX"] + APIDATA["configVector"]["headPositionX"] + CabinOffsetX
    HeadOffsetY = APIDATA["headPlacement"]["headOffsetY"] + APIDATA["configVector"]["headPositionY"] + CabinOffsetY
    HeadOffsetZ = APIDATA["headPlacement"]["headOffsetZ"] + APIDATA["configVector"]["headPositionZ"] + CabinOffsetZ
    HeadOffsetRotationX = APIDATA["headPlacement"]["headOffsetrotationX"]
    HeadOffsetRotationY = APIDATA["headPlacement"]["headOffsetrotationY"]
    HeadOffsetRotationZ = 0

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


    OffsetX = 70
    OffsetZ = 15

    PointX = TruckX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = TruckY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = TruckZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        TopLeft = X, Y
        Points.append((PointX, PointZ))


    OffsetX = 70
    OffsetZ = -15

    PointX = TruckX + OffsetX * math.sin(TruckRotationRadiansX) - OffsetZ * math.cos(TruckRotationRadiansX)
    PointY = TruckY + math.tan(math.radians(TruckRotationY * 360)) * math.sqrt(OffsetX**2 + OffsetZ**2)
    PointZ = TruckZ - OffsetX * math.cos(TruckRotationRadiansX) - OffsetZ * math.sin(TruckRotationRadiansX)

    X, Y, D = ConvertToScreenCoordinate(PointX, PointY, PointZ)
    if X == None or Y == None:
        AllCoordinatesValid = False
    else:
        TopRight = X, Y
        Points.append((PointX, PointZ))


    OffsetX = 15
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


    OffsetX = 15
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

    if AllCoordinatesValid and False:
        cv2.circle(Frame, (round(TopLeft[0]), round(TopLeft[1])), 5, (0, 0, 255), -1)
        cv2.circle(Frame, (round(TopRight[0]), round(TopRight[1])), 5, (0, 0, 255), -1)
        cv2.circle(Frame, (round(BottomLeft[0]), round(BottomLeft[1])), 5, (0, 0, 255), -1)
        cv2.circle(Frame, (round(BottomRight[0]), round(BottomRight[1])), 5, (0, 0, 255), -1)

    if AllCoordinatesValid:
        CroppedWidth = round(max(TopRight[0] - TopLeft[0], BottomRight[0] - BottomLeft[0]))
        CroppedHeight = round(max(BottomLeft[1] - TopLeft[1], BottomRight[1] - TopRight[1]))
        SourcePoints = np.float32([TopLeft, TopRight, BottomLeft, BottomRight])
        DestinationPoints = np.float32([[0, 0], [CroppedWidth, 0], [0, CroppedHeight], [CroppedWidth, CroppedHeight]])
        Matrix = cv2.getPerspectiveTransform(SourcePoints, DestinationPoints)
        Frame = cv2.warpPerspective(Frame, Matrix, (CroppedWidth, CroppedHeight))


    # frame = cv2.resize(frame, (100, 100))
    # image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # image = np.array(image, dtype=np.float32) / 255.0
    # transform = transforms.Compose([
    #     transforms.ToTensor(),
    # ])
    # image = transform(image).unsqueeze(0)
    # with torch.no_grad():
    #     prediction = model(image.to(device))

    # prediction = prediction.squeeze(0).permute(1, 2, 0).cpu().numpy()

    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    # prediction_overlay = cv2.cvtColor(prediction, cv2.COLOR_GRAY2BGRA)

    # prediction_overlay[:, :, 2] = 0
    # prediction_overlay = prediction_overlay.astype(np.uint8) * 255

    # frame = cv2.addWeighted(frame, 1, prediction_overlay, 0.5, 0)

    # non_black_pixels = np.where(prediction_overlay[:, :, 0] != 0)
    # if len(non_black_pixels[0]) > 0:
    #     x_center = int(np.mean(non_black_pixels[1]))
    # else:
    #     x_center = width // 2
    # cv2.line(frame, (x_center, 0), (x_center, height), (0, 255, 0), 1)



    # Steering = (x_center/frame.shape[1] - 0.5) * 0.3 - 0.0125

    # SteeringHistory.append((Steering, CurrentTime))
    # SteeringHistory.sort(key=lambda x: x[1])
    # while CurrentTime - SteeringHistory[0][1] > 0.2:
    #     SteeringHistory.pop(0)
    # Steering = sum(x[0] for x in SteeringHistory) / len(SteeringHistory)

    # SDKController.steering = float(Steering)

    ShowImage.Show("AdaptiveCruiseControl", Frame)