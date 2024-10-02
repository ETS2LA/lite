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

    hwnd = win32gui.FindWindow(None, 'ETS2LA - AR/Overlay')
    margins = MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, margins)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)


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


def ConvertToScreenCoordinate(x: float, y: float, z: float):
    head_yaw = head_rotation_degrees_x
    head_pitch = head_rotation_degrees_y
    head_roll = head_rotation_degrees_z

    rel_x = x - head_x
    rel_y = y - head_y
    rel_z = z - head_z

    cos_yaw = math.cos(math.radians(-head_yaw))
    sin_yaw = math.sin(math.radians(-head_yaw))
    new_x = rel_x * cos_yaw + rel_z * sin_yaw
    new_z = rel_z * cos_yaw - rel_x * sin_yaw

    cos_pitch = math.cos(math.radians(-head_pitch))
    sin_pitch = math.sin(math.radians(-head_pitch))
    new_y = rel_y * cos_pitch - new_z * sin_pitch
    final_z = new_z * cos_pitch + rel_y * sin_pitch

    cos_roll = math.cos(math.radians(head_roll))
    sin_roll = math.sin(math.radians(head_roll))
    final_x = new_x * cos_roll - new_y * sin_roll
    final_y = new_y * cos_roll + new_x * sin_roll

    if final_z >= 0:
        return None, None, None

    fov_rad = math.radians(variables.FOV)
    
    window_distance = ((WindowPosition[3] - WindowPosition[1]) * (4 / 3) / 2) / math.tan(fov_rad / 2)

    screen_x = (final_x / final_z) * window_distance + (WindowPosition[2] - WindowPosition[0]) / 2
    screen_y = (final_y / final_z) * window_distance + (WindowPosition[3] - WindowPosition[1]) / 2

    screen_x = (WindowPosition[2] - WindowPosition[0]) - screen_x

    distance = math.sqrt((rel_x ** 2) + (rel_y ** 2) + (rel_z ** 2))

    return screen_x, screen_y, distance


def Run(data):
    global LastWindowPosition
    global WindowPosition

    global head_rotation_degrees_x
    global head_rotation_degrees_y
    global head_rotation_degrees_z
    global head_x
    global head_y
    global head_z

    data = {}
    data["api"] = TruckSimAPI.update()

    WindowPosition = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
    if LastWindowPosition != WindowPosition:
        Resize()


    truck_x = data["api"]["truckPlacement"]["coordinateX"]
    truck_y = data["api"]["truckPlacement"]["coordinateY"]
    truck_z = data["api"]["truckPlacement"]["coordinateZ"]
    truck_rotation_x = data["api"]["truckPlacement"]["rotationX"]
    truck_rotation_y = data["api"]["truckPlacement"]["rotationY"]
    truck_rotation_z = data["api"]["truckPlacement"]["rotationZ"]

    cabin_offset_x = data["api"]["headPlacement"]["cabinOffsetX"] + data["api"]["configVector"]["cabinPositionX"]
    cabin_offset_y = data["api"]["headPlacement"]["cabinOffsetY"] + data["api"]["configVector"]["cabinPositionY"]
    cabin_offset_z = data["api"]["headPlacement"]["cabinOffsetZ"] + data["api"]["configVector"]["cabinPositionZ"]
    cabin_offset_rotation_x = data["api"]["headPlacement"]["cabinOffsetrotationX"]
    cabin_offset_rotation_y = data["api"]["headPlacement"]["cabinOffsetrotationY"]
    cabin_offset_rotation_z = data["api"]["headPlacement"]["cabinOffsetrotationZ"]

    head_offset_x = data["api"]["headPlacement"]["headOffsetX"] + data["api"]["configVector"]["headPositionX"] + cabin_offset_x
    head_offset_y = data["api"]["headPlacement"]["headOffsetY"] + data["api"]["configVector"]["headPositionY"] + cabin_offset_y
    head_offset_z = data["api"]["headPlacement"]["headOffsetZ"] + data["api"]["configVector"]["headPositionZ"] + cabin_offset_z
    head_offset_rotation_x = data["api"]["headPlacement"]["headOffsetrotationX"]
    head_offset_rotation_y = data["api"]["headPlacement"]["headOffsetrotationY"]
    head_offset_rotation_z = data["api"]["headPlacement"]["headOffsetrotationZ"]

    truck_rotation_degrees_x = truck_rotation_x * 360
    truck_rotation_radians_x = -math.radians(truck_rotation_degrees_x)

    head_rotation_degrees_x = (truck_rotation_x + cabin_offset_rotation_x + head_offset_rotation_x) * 360
    while head_rotation_degrees_x > 360:
        head_rotation_degrees_x = head_rotation_degrees_x - 360

    head_rotation_degrees_y = (truck_rotation_y + cabin_offset_rotation_y + head_offset_rotation_y) * 360

    head_rotation_degrees_z = (truck_rotation_z + cabin_offset_rotation_z + head_offset_rotation_z) * 360

    point_x = head_offset_x
    point_y = head_offset_y
    point_z = head_offset_z
    head_x = point_x * math.cos(truck_rotation_radians_x) - point_z * math.sin(truck_rotation_radians_x) + truck_x
    head_y = point_y * math.cos(math.radians(head_rotation_degrees_y)) - point_z * math.sin(math.radians(head_rotation_degrees_y)) + truck_y
    head_z = point_x * math.sin(truck_rotation_radians_x) + point_z * math.cos(truck_rotation_radians_x) + truck_z


    x1, y1, d1 = ConvertToScreenCoordinate(x=10448.742, y=35.324, z=-10132.315)

    x2, y2, d2 = ConvertToScreenCoordinate(x=10453.237, y=36.324, z=-10130.404)

    x3, y3, d3 = ConvertToScreenCoordinate(x=10453.237, y=34.324, z=-10130.404)
    
    Alpha = CalculateAlpha(Distances=(d1, d2, d3))


    DrawRectangle(X1=0, Y1=0, X2=100, Y2=100, Color=(255, 255, 255), Thickness=2)
    DrawLine(X1=0, Y1=0, X2=100, Y2=100, Color=(255, 255, 255), Thickness=2)
    DrawPolygon(Points=[(125, 0), (125, 125), (0, 125)], Color=(255, 255, 255), FillColor=(0, 0, 0, 127), Thickness=2, Closed=False)
    DrawCircle(X=0, Y=0, R=100, Color=(255, 255, 255), FillColor=(0, 0, 0, 127), Thickness=2)

    DrawPolygon(Points=[(x1, y1), (x2, y2), (x3, y3)], Color=(255, 255, 255, Alpha), FillColor=(127, 127, 127, Alpha / 2), Thickness=2, Closed=True)

    Render()