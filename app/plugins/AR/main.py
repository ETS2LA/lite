from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
import modules.ScreenCapture.main as ScreenCapture
from modules.Camera.main import SCSCamera
import src.variables as variables

import dearpygui.dearpygui as dpg
import multiprocessing
import keyboard
import win32con
import win32gui
import ctypes
import math
import time


PROCESS = multiprocessing.current_process().name


global A, Alpha, B, Beta, BRotation, C
A = None, None
Alpha = None
B = None, None
BRotation = 0
Beta = None
C = None, None


def Initialize():
    global Camera
    global TruckSimAPI
    global LastWindowPosition
    global DRAWLIST
    global FRAME
    global FOV
    Camera = SCSCamera()
    TruckSimAPI = SCSTelemetry()
    LastWindowPosition = None, None, None, None
    DRAWLIST = []
    FRAME = None

    FOV = Camera.update().fov
    InitializeWindow()


def InitializeWindow():
    WindowX1, WindowY1, WindowX2, WindowY2 = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])

    dpg.create_context()
    dpg.create_viewport(title=f'ETS2LA-Lite AR Overlay', always_on_top=True, decorated=False, clear_color=[0.0,0.0,0.0,0.0], vsync=False, x_pos=WindowX1, y_pos=WindowY1, width=WindowX2-WindowX1, height=WindowY2-WindowY1, small_icon=f"{variables.Path}app/assets/favicon.ico", large_icon=f"{variables.Path}app/assets/favicon.ico")
    dpg.set_viewport_always_top(True)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    class MARGINS(ctypes.Structure):
        _fields_ = [("cxLeftWidth", ctypes.c_int),
                    ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int),
                    ("cyBottomHeight", ctypes.c_int)]

    HWND = win32gui.FindWindow(None, 'ETS2LA-Lite AR Overlay')
    Margins = MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(HWND, Margins)
    win32gui.SetWindowLong(HWND, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(HWND, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)


def Resize():
    dpg.set_viewport_pos([WindowPosition[0], WindowPosition[1]])
    dpg.set_viewport_width(WindowPosition[2] - WindowPosition[0])
    dpg.set_viewport_height(WindowPosition[3] - WindowPosition[1])


def DrawRectangle(Start=[0, 0] if PROCESS == "AR" else [0, 0, 0], End=[100, 100] if PROCESS == "AR" else [1, 1, 1], Color=[255, 255, 255, 255], FillColor=[0, 0, 0, 0], Thickness=1):
    global DRAWLIST
    FillColor = list(FillColor)
    Color = list(Color)
    if len(FillColor) <= 3:
        FillColor.append(255)
    if len(Color) <= 3:
        Color.append(255)
    if PROCESS == "AR":
        DRAWLIST.append(("Rectangle", Start, End, Color, FillColor, Thickness))
    else:
        return ["DrawRectangle", Start, End, Color, FillColor, Thickness]


def DrawLine(Start=[0, 0] if PROCESS == "AR" else [0, 0, 0], End=[100, 100] if PROCESS == "AR" else [1, 1, 1], Color=[255, 255, 255, 255], Thickness=1):
    global DRAWLIST
    Color = list(Color)
    if len(Color) <= 3:
        Color.append(255)
    if PROCESS == "AR":
        DRAWLIST.append(("Line", Start, End, Color, Thickness))
    else:
        return ["DrawLine", Start, End, Color, Thickness]


def DrawPolygon(Points=[(100, 0), (100, 100), (0, 100)] if PROCESS == "AR" else [(1, 0, 0), (0, 1, 0), (0, 0, 1)], Color=[255, 255, 255, 255], FillColor=[0, 0, 0, 0], Thickness=1, Closed=False):
    global DRAWLIST
    FillColor = list(FillColor)
    Color = list(Color)
    if len(FillColor) <= 3:
        FillColor.append(255)
    if len(Color) <= 3:
        Color.append(255)
    if PROCESS == "AR":
        Points = [(X, Y) for X, Y in Points if X != None and Y != None]
    else:
        Points = [(X, Y, Z) for X, Y, Z in Points if X != None and Y != None and Z != None]
    if len(Points) <= 1:
        return
    if Closed:
        if Points[0] != Points[-1]:
            Points.append(Points[0])
    if PROCESS == "AR":
        DRAWLIST.append(("Polygon", Points, Color, FillColor, Thickness))
    else:
        return ["DrawPolygon", Points, Color, FillColor, Thickness, Closed]


def DrawCircle(Center=[0, 0] if PROCESS == "AR" else [0, 0, 0], R=100, Color=[255, 255, 255, 255], FillColor=[0, 0, 0, 0], Thickness=1):
    global DRAWLIST
    Color = list(Color)
    if len(Color) <= 3:
        Color.append(255)
    if PROCESS == "AR":
        DRAWLIST.append(("Circle", Center, R, Color, FillColor, Thickness))
    else:
        return ["DrawCircle", Center, R, Color, FillColor, Thickness]


def Render():
    global FRAME
    global DRAWLIST
    dpg.delete_item(FRAME)
    with dpg.viewport_drawlist(label="draw") as FRAME:
        for Item in DRAWLIST:
            if Item[0] == "Rectangle":
                dpg.draw_rectangle(pmin=Item[1], pmax=Item[2], color=Item[3], fill=Item[4], thickness=Item[5])
            elif Item[0] == "Line":
                dpg.draw_line(p1=Item[1], p2=Item[2], color=Item[3], thickness=Item[4])
            elif Item[0] == "Polygon":
                dpg.draw_polygon(points=Item[1], color=Item[2], fill=Item[3], thickness=Item[4])
            elif Item[0] == "Circle":
                dpg.draw_circle(center=Item[1], radius=Item[2], color=Item[3], fill=Item[4], thickness=Item[5])
    dpg.render_dearpygui_frame()
    DRAWLIST = []


def CalculateAlpha(Distances=()):
    Distances = [Distance for Distance in Distances if Distance != None]
    if len(Distances) == 0:
        return 0
    AverageDistance = sum(Distances) / len(Distances)
    if AverageDistance < 10:
        return 0
    elif 10 <= AverageDistance < 30:
        return (255 * (AverageDistance - 10) / 20)
    elif 30 <= AverageDistance < 150:
        return 255
    elif 150 <= AverageDistance < 170:
        return (255 * (170 - AverageDistance) / 20)
    else:
        return 0


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

    CosRoll = math.cos(math.radians(-HeadRoll))
    SinRoll = math.sin(math.radians(-HeadRoll))
    FinalX = NewX * CosRoll - NewY * SinRoll
    FinalY = NewY * CosRoll + NewX * SinRoll

    if FinalZ >= 0:
        return None, None, None

    FovRad = math.radians(FOV)
    if FovRad <= 0:
        return None, None, None

    WindowDistance = ((WindowPosition[3] - WindowPosition[1]) * (4 / 3) / 2) / math.tan(FovRad / 2)

    ScreenX = (FinalX / FinalZ) * WindowDistance + (WindowPosition[2] - WindowPosition[0]) / 2
    ScreenY = (FinalY / FinalZ) * WindowDistance + (WindowPosition[3] - WindowPosition[1]) / 2

    ScreenX = (WindowPosition[2] - WindowPosition[0]) - ScreenX

    Distance = math.sqrt((RelativeX ** 2) + (RelativeY ** 2) + (RelativeZ ** 2))

    return ScreenX, ScreenY, Distance


def ConvertToAngle(X, Y):
    if X == None or Y == None:
        return 0, 0
    _, _, WindowWidth, WindowHeight = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
    WindowDistance = ((WindowPosition[3] - WindowPosition[1]) * (4 / 3) / 2) / math.tan(math.radians(FOV) / 2)
    AngleX = math.atan2(X - WindowWidth / 2, WindowDistance) * (180 / math.pi)
    AngleY = math.atan2(Y - WindowHeight / 2, WindowDistance) * (180 / math.pi)
    HeadRotationX = HeadOffsetRotationX * 360
    HeadRotationX = HeadRotationX - 360 if HeadRotationX > 180 else HeadRotationX
    HeadRotationY = HeadOffsetRotationY * 360
    HeadRotationY = HeadRotationY - 360 if HeadRotationY > 180 else HeadRotationY
    AngleX = -HeadRotationX + AngleX
    AngleY = -HeadRotationY + AngleY
    return AngleX, AngleY


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


def ArcTan(Value):
    return math.degrees(math.atan(Value))


def Cos(Value):
    return math.cos(math.radians(Value))


def Sin(Value):
    return math.sin(math.radians(Value))


def Run(Data):
    global LastWindowPosition
    global WindowPosition

    global HeadRotationDegreesX
    global HeadRotationDegreesY
    global HeadRotationDegreesZ
    global HeadOffsetRotationX
    global HeadOffsetRotationY
    global HeadX
    global HeadY
    global HeadZ

    APIDATA = TruckSimAPI.update()

    if APIDATA["pause"] == True or ScreenCapture.IsForegroundWindow(Name="Truck Simulator", Blacklist=["Discord"]) == False:
        time.sleep(0.1)
        Render()
        return

    WindowPosition = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
    if LastWindowPosition != WindowPosition:
        Resize()


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

    HeadRotationDegreesZ = (TruckRotationZ + CabinOffsetRotationZ + HeadOffsetRotationZ) * 180

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
        X, Y, D = ConvertToScreenCoordinate(X=PointX, Y=PointY, Z=PointZ)
        DrawCircle(Center=(X, Y), R=10, Color=(255, 255, 255), FillColor=(127, 127, 127, 127), Thickness=2)


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


        Wheels = [FrontLeftWheel, FrontRightWheel, BackLeftWheel, BackRightWheel]
        for i in range(len(Wheels)):
            Wheel = Wheels[i]
            X, Y, D = ConvertToScreenCoordinate(X=Wheel[0], Y=TruckY, Z=Wheel[2])
            if i % 2 == 0:
                Color = (255, 0, 0)
            else:
                Color = (0, 0, 255)
            DrawCircle(Center=(X, Y), R=10, Color=Color, FillColor=(127, 127, 127, 127), Thickness=2)


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

        for i in range(2):
            if i == 0:
                R = LeftFrontWheelRadius
                CenterX = LeftCenterX
                CenterZ = LeftCenterZ
                Offset = math.degrees(math.atan(DistanceLeft / R))
            else:
                R = RightFrontWheelRadius
                CenterX = RightCenterX
                CenterZ = RightCenterZ
                Offset = math.degrees(math.atan(DistanceRight / R))
            Points = []
            for j in range(45):
                Angle = j * (1 / -R) * 30 - TruckRotationDegreesX - Offset
                Angle = math.radians(Angle)
                X = CenterX + R * math.cos(Angle)
                Z = CenterZ + R * math.sin(Angle)
                Distance = math.sqrt((X - TruckX) ** 2 + (Z - TruckZ) ** 2)
                Y = TruckY + math.tan(math.radians(TruckRotationY * 360)) * Distance
                X, Y, D = ConvertToScreenCoordinate(X=X, Y=Y, Z=Z)
                Points.append((X, Y))
                #if D != None and D < 50:
                #    DrawCircle(Center=(X, Y), R=10, Color=(0, 255, 255), FillColor=(127, 127, 127, 127), Thickness=2)
            DrawPolygon(Points=Points, Color=(0, 255, 255), Thickness=2)


    #X1, Y1, D1 = ConvertToScreenCoordinate(X=10448.742, Y=35.324, Z=-10132.315)
    #X2, Y2, D2 = ConvertToScreenCoordinate(X=10453.237, Y=36.324, Z=-10130.404)
    #X3, Y3, D3 = ConvertToScreenCoordinate(X=10453.237, Y=34.324, Z=-10130.404)
    #Alpha = CalculateAlpha(Distances=(D1, D2, D3))

    #DrawRectangle(X1=0, Y1=0, X2=100, Y2=100, Color=(255, 255, 255), Thickness=2)
    #DrawLine(X1=0, Y1=0, X2=100, Y2=100, Color=(255, 255, 255), Thickness=2)
    #DrawPolygon(Points=[(125, 0), (125, 125), (0, 125)], Color=(255, 255, 255), FillColor=(0, 0, 0, 127), Thickness=2, Closed=False)
    #DrawCircle(X=0, Y=0, R=100, Color=(255, 255, 255), FillColor=(0, 0, 0, 127), Thickness=2)
    #DrawPolygon(Points=[(X1, Y1), (X2, Y2), (X3, Y3)], Color=(255, 255, 255, Alpha), FillColor=(127, 127, 127, Alpha / 2), Thickness=2, Closed=True)


    TargetX = 10361.64
    TargetY = 44.34
    TargetZ = -9230.61

    X, Y, D = ConvertToScreenCoordinate(X=TargetX, Y=TargetY, Z=TargetZ)
    DrawCircle(Center=(X, Y), R=10, Color=(0, 255, 0), FillColor=(0, 127, 0, 127), Thickness=2)

    global A, Alpha, B, Beta, BRotation, C

    A = HeadX, HeadZ
    ScreenX, ScreenY, _ = ConvertToScreenCoordinate(X=TargetX, Y=TargetY, Z=TargetZ)
    Alpha = ConvertToAngle(X=ScreenX, Y=ScreenY)[0]


    if keyboard.is_pressed("x"):
        B = HeadX, HeadZ
        BRotation = TruckRotationDegreesX
        ScreenX, ScreenY, _ = ConvertToScreenCoordinate(X=TargetX, Y=TargetY, Z=TargetZ)
        Beta = ConvertToAngle(X=ScreenX, Y=ScreenY)[0]


    if A != (None, None) and Alpha != None and B != (None, None) and Beta != None:
        try:

            AngleAB = 0
            DistanceAB = math.sqrt((B[0] - A[0]) ** 2 + (B[1] - A[1]) ** 2)

            TempAlpha = 180 - Alpha - AngleAB
            TempBeta = Beta + AngleAB

            #print(f"AngleAB: {round(AngleAB, 1)}, DistanceAB: {round(DistanceAB, 1)}, TempAlpha: {round(TempAlpha, 1)}, TempBeta: {round(TempBeta, 1)}")

            b = abs((DistanceAB / Sin(180 - TempAlpha - TempBeta)) * Sin(TempBeta))

            OffsetX = Sin(Alpha) * b
            OffsetZ = Cos(Alpha) * -b

            Cx = A[0] + OffsetX * Cos(TruckRotationDegreesX) + OffsetZ * Sin(TruckRotationDegreesX)
            Cy = A[1] + OffsetZ * Cos(TruckRotationDegreesX) - OffsetX * Sin(TruckRotationDegreesX)

            C = Cx, Cy

            #print(f"True: X: {round(TargetX, 1)} Z: {round(TargetZ, 1)} Calculated: X: {round(C[0], 1)} Z: {round(C[1], 1)}, Alpha: {round(Alpha, 1)}, Beta: {round(Beta, 1)}, OffsetX: {round(Sin(Alpha) * b, 1)}, OffsetZ: {round(Cos(Alpha) * b, 1)}, b: {round(b, 1)}")

        except:
            pass

    if C != (None, None):
        ScreenX, ScreenY, _ = ConvertToScreenCoordinate(X=C[0], Y=TargetY, Z=C[1])
        DrawCircle(Center=(ScreenX, ScreenY), R=10, Color=(255, 0, 0), FillColor=(127, 0, 0, 127), Thickness=2)




    for Plugin in Data.items():
        if "AR" in Plugin[1]:
            for Item in Plugin[1]["AR"]:
                if Item[0] == "DrawRectangle":
                    X1, Y1, D1 = ConvertToScreenCoordinate(X=Item[1], Y=Item[2], Z=Item[3])
                    X2, Y2, D2 = ConvertToScreenCoordinate(X=Item[4], Y=Item[5], Z=Item[6])
                    DrawRectangle(Start=(X1, Y1), End=(X2, Y2), Color=Item[7], FillColor=Item[8], Thickness=Item[9])
                elif Item[0] == "DrawLine":
                    X1, Y1, D1 = ConvertToScreenCoordinate(X=Item[1], Y=Item[2], Z=Item[3])
                    X2, Y2, D2 = ConvertToScreenCoordinate(X=Item[4], Y=Item[5], Z=Item[6])
                    DrawLine(Start=(X1, Y1), End=(X2, Y2), Color=Item[7], Thickness=Item[8])
                elif Item[0] == "DrawPolygon":
                    Points = [ConvertToScreenCoordinate(X=Point[0], Y=Point[1], Z=Point[2])[0:2] for Point in Item[1]]
                    DrawPolygon(Points=Points, Color=Item[2], FillColor=Item[3], Thickness=Item[4])
                elif Item[0] == "DrawCircle":
                    X, Y, D = ConvertToScreenCoordinate(X=Item[1], Y=Item[2], Z=Item[3])
                    DrawCircle(Center=(X, Y), R=Item[4], Color=Item[5], FillColor=Item[6], Thickness=Item[7])

    Render()