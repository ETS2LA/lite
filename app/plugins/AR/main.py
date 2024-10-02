from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
import modules.ScreenCapture.main as ScreenCapture
import src.variables as variables
import src.settings as settings

import dearpygui.dearpygui as dpg
import ctypes
import math
import time

if variables.OS == "nt":
    import win32con
    import win32gui


def Initialize():
    global TruckSimAPI
    global LastWindowPosition
    global DRAWLIST
    global FRAME
    TruckSimAPI = SCSTelemetry()
    LastWindowPosition = None, None, None, None
    DRAWLIST = []
    FRAME = None
    InitializeWindow()


def InitializeWindow():
    WindowX1, WindowY1, WindowX2, WindowY2 = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])

    dpg.create_context()
    dpg.create_viewport(title=f'ETS2LA - AR/Overlay', always_on_top=True, decorated=False, clear_color=[0.0,0.0,0.0,0.0], vsync=False, x_pos=WindowX1, y_pos=WindowY1, width=WindowX2-WindowX1, height=WindowY2-WindowY1, small_icon=f"{variables.PATH}app/assets/favicon.ico", large_icon=f"{variables.PATH}app/assets/favicon.ico")
    dpg.set_viewport_always_top(True)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    class MARGINS(ctypes.Structure):
        _fields_ = [("cxLeftWidth", ctypes.c_int),
                    ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int),
                    ("cyBottomHeight", ctypes.c_int)]

    HWND = win32gui.FindWindow(None, 'ETS2LA - AR/Overlay')
    Margins = MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(HWND, Margins)
    win32gui.SetWindowLong(HWND, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(HWND, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)


def Resize():
    dpg.set_viewport_pos([WindowPosition[0], WindowPosition[1]])
    dpg.set_viewport_width(WindowPosition[2] - WindowPosition[0])
    dpg.set_viewport_height(WindowPosition[3] - WindowPosition[1])


def DrawRectangle(X1=0, Y1=0, X2=100, Y2=100, Color=[255, 255, 255, 255], FillColor=[0, 0, 0, 0], Thickness=1):
    global DRAWLIST
    FillColor = list(FillColor)
    Color = list(Color)
    if len(FillColor) <= 3:
        FillColor.append(255)
    if len(Color) <= 3:
        Color.append(255)
    DRAWLIST.append(("Rectangle", [X1, Y1], [X2, Y2], Color, FillColor, Thickness))


def DrawLine(X1=0, Y1=0, X2=100, Y2=100, Color=[255, 255, 255, 255], Thickness=1):
    global DRAWLIST
    Color = list(Color)
    if len(Color) <= 3:
        Color.append(255)
    DRAWLIST.append(("Line", [X1, Y1], [X2, Y2], Color, Thickness))


def DrawPolygon(Points=[(100, 0), (100, 100), (0, 100)], Color=[255, 255, 255, 255], FillColor=[0, 0, 0, 0], Thickness=1, Closed=False):
    global DRAWLIST
    FillColor = list(FillColor)
    Color = list(Color)
    if len(FillColor) <= 3:
        FillColor.append(255)
    if len(Color) <= 3:
        Color.append(255)
    Points = [(X, Y) for X, Y in Points if X != None and Y != None]
    if len(Points) <= 1:
        return
    if Closed:
        if Points[0] != Points[-1]:
            Points.append(Points[0])
    DRAWLIST.append(("Polygon", Points, Color, FillColor, Thickness))


def DrawCircle(X=0, Y=0, R=100, Color=[255, 255, 255, 255], FillColor=[0, 0, 0, 0], Thickness=1):
    global DRAWLIST
    Color = list(Color)
    if len(Color) <= 3:
        Color.append(255)
    DRAWLIST.append(("Circle", [X, Y], R, Color, FillColor, Thickness))


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

    CosRoll = math.cos(math.radians(HeadRoll))
    SinRoll = math.sin(math.radians(HeadRoll))
    FinalX = NewX * CosRoll - NewY * SinRoll
    FinalY = NewY * CosRoll + NewX * SinRoll

    if FinalZ >= 0:
        return None, None, None

    FovRad = math.radians(variables.FOV)
    
    WindowDistance = ((WindowPosition[3] - WindowPosition[1]) * (4 / 3) / 2) / math.tan(FovRad / 2)

    ScreenX = (FinalX / FinalZ) * WindowDistance + (WindowPosition[2] - WindowPosition[0]) / 2
    ScreenY = (FinalY / FinalZ) * WindowDistance + (WindowPosition[3] - WindowPosition[1]) / 2

    ScreenX = (WindowPosition[2] - WindowPosition[0]) - ScreenX

    Distance = math.sqrt((RelativeX ** 2) + (RelativeY ** 2) + (RelativeZ ** 2))

    return ScreenX, ScreenY, Distance


def Run(Data):
    global LastWindowPosition
    global WindowPosition

    global HeadRotationDegreesX
    global HeadRotationDegreesY
    global HeadRotationDegreesZ
    global HeadX
    global HeadY
    global HeadZ

    Data = {}
    Data["api"] = TruckSimAPI.update()

    if Data["api"]["pause"] == True or ScreenCapture.IsForegroundWindow(Name="Truck Simulator", Blacklist=["Discord"]) == False:
        time.sleep(0.1)
        Render()
        return

    WindowPosition = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
    if LastWindowPosition != WindowPosition:
        Resize()


    TruckX = Data["api"]["truckPlacement"]["coordinateX"]
    TruckY = Data["api"]["truckPlacement"]["coordinateY"]
    TruckZ = Data["api"]["truckPlacement"]["coordinateZ"]
    TruckRotationX = Data["api"]["truckPlacement"]["rotationX"]
    TruckRotationY = Data["api"]["truckPlacement"]["rotationY"]
    TruckRotationZ = Data["api"]["truckPlacement"]["rotationZ"]

    CabinOffsetX = Data["api"]["headPlacement"]["cabinOffsetX"] + Data["api"]["configVector"]["cabinPositionX"]
    CabinOffsetY = Data["api"]["headPlacement"]["cabinOffsetY"] + Data["api"]["configVector"]["cabinPositionY"]
    CabinOffsetZ = Data["api"]["headPlacement"]["cabinOffsetZ"] + Data["api"]["configVector"]["cabinPositionZ"]
    CabinOffsetRotationX = Data["api"]["headPlacement"]["cabinOffsetrotationX"]
    CabinOffsetRotationY = Data["api"]["headPlacement"]["cabinOffsetrotationY"]
    CabinOffsetRotationZ = Data["api"]["headPlacement"]["cabinOffsetrotationZ"]

    HeadOffsetX = Data["api"]["headPlacement"]["headOffsetX"] + Data["api"]["configVector"]["headPositionX"] + CabinOffsetX
    HeadOffsetY = Data["api"]["headPlacement"]["headOffsetY"] + Data["api"]["configVector"]["headPositionY"] + CabinOffsetY
    HeadOffsetZ = Data["api"]["headPlacement"]["headOffsetZ"] + Data["api"]["configVector"]["headPositionZ"] + CabinOffsetZ
    HeadOffsetRotationX = Data["api"]["headPlacement"]["headOffsetrotationX"]
    HeadOffsetRotationY = Data["api"]["headPlacement"]["headOffsetrotationY"]
    HeadOffsetRotationZ = Data["api"]["headPlacement"]["headOffsetrotationZ"]

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


    TruckWheelPointsX = [Point for Point in Data["api"]["configVector"]["truckWheelPositionX"] if Point != 0]
    TruckWheelPointsY = [Point for Point in Data["api"]["configVector"]["truckWheelPositionY"] if Point != 0]
    TruckWheelPointsZ = [Point for Point in Data["api"]["configVector"]["truckWheelPositionZ"] if Point != 0]

    WheelAngles = [Angle for Angle in Data["api"]["truckFloat"]["truck_wheelSteering"] if Angle != 0]
    while int(Data["api"]["configUI"]["truckWheelCount"]) > len(WheelAngles):
        WheelAngles.append(0)

    for i in range(len(TruckWheelPointsX)):
        PointX = TruckX + TruckWheelPointsX[i] * math.cos(TruckRotationRadiansX) - TruckWheelPointsZ[i] * math.sin(TruckRotationRadiansX)
        PointY = TruckY + TruckWheelPointsY[i]
        PointZ = TruckZ + TruckWheelPointsZ[i] * math.cos(TruckRotationRadiansX) + TruckWheelPointsX[i] * math.sin(TruckRotationRadiansX)
        X, Y, D = ConvertToScreenCoordinate(X=PointX, Y=PointY, Z=PointZ)
        DrawCircle(X=X, Y=Y, R=10, Color=(255, 255, 255), FillColor=(127, 127, 127, 127), Thickness=2)


    X1, Y1, D1 = ConvertToScreenCoordinate(X=10448.742, Y=35.324, Z=-10132.315)

    X2, Y2, D2 = ConvertToScreenCoordinate(X=10453.237, Y=36.324, Z=-10130.404)

    X3, Y3, D3 = ConvertToScreenCoordinate(X=10453.237, Y=34.324, Z=-10130.404)

    Alpha = CalculateAlpha(Distances=(D1, D2, D3))


    DrawRectangle(X1=0, Y1=0, X2=100, Y2=100, Color=(255, 255, 255), Thickness=2)
    DrawLine(X1=0, Y1=0, X2=100, Y2=100, Color=(255, 255, 255), Thickness=2)
    DrawPolygon(Points=[(125, 0), (125, 125), (0, 125)], Color=(255, 255, 255), FillColor=(0, 0, 0, 127), Thickness=2, Closed=False)
    DrawCircle(X=0, Y=0, R=100, Color=(255, 255, 255), FillColor=(0, 0, 0, 127), Thickness=2)

    DrawPolygon(Points=[(X1, Y1), (X2, Y2), (X3, Y3)], Color=(255, 255, 255, Alpha), FillColor=(127, 127, 127, Alpha / 2), Thickness=2, Closed=True)

    Render()