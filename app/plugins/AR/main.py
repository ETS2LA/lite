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
    global Fov
    global LastWindowPosition
    global FRAME
    TruckSimAPI = SCSTelemetry()
    Fov = settings.Get("AR", "FOV", 80)
    LastWindowPosition = None, None, None, None
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
    dwm = ctypes.windll.dwmapi
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, margins)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)


def Resize():
    dpg.set_viewport_pos([WindowPosition[0], WindowPosition[1]])
    dpg.set_viewport_width(WindowPosition[2] - WindowPosition[0])
    dpg.set_viewport_height(WindowPosition[3] - WindowPosition[1])


def DrawRectangle(X1=0, Y1=0, X2=100, Y2=100, Color=[0, 255, 0, 255], FillColor=[0, 0, 0, 0], Thickness=5):
    global FRAME
    FillColor = list(FillColor)
    Color = list(Color)
    if len(FillColor) <= 3:
        FillColor.append(255)
    if len(Color) <= 3:
        Color.append(255)
    with dpg.viewport_drawlist(label="draw") as FRAME:
        dpg.draw_rectangle([X1 * (WindowPosition[2] - WindowPosition[0]), Y1 * (WindowPosition[3] - WindowPosition[1])], [X2 * (WindowPosition[2] - WindowPosition[0]), Y2 * (WindowPosition[3] - WindowPosition[1])], fill=FillColor, color=Color, thickness=Thickness)


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

    fov_rad = math.radians(Fov)
    
    window_distance = ((WindowPosition[3] - WindowPosition[1]) * (4 / 3) / 2) / math.tan(fov_rad / 2)

    screen_x = (final_x / final_z) * window_distance + (WindowPosition[2] - WindowPosition[0]) / 2
    screen_y = (final_y / final_z) * window_distance + (WindowPosition[3] - WindowPosition[1]) / 2

    screen_x = (WindowPosition[2] - WindowPosition[0]) - screen_x

    distance = math.sqrt((rel_x ** 2) + (rel_y ** 2) + (rel_z ** 2))

    return screen_x, screen_y, distance


def Run(data):
    global FRAME
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

    if FRAME is not None:
        dpg.delete_item(FRAME)


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
    
    alpha_zones = [(30, 10, 255), (150, float('inf'), lambda x: 255 - int((x - 10) / 20 * 255))]

    def calculate_alpha(avg_d):
        for zone in alpha_zones:
            if avg_d < zone[1]:
                if callable(zone[2]):
                    return zone[2](avg_d)
                else:
                    return zone[2]
        return 0

    if d1 != None and d2 != None and d3 != None:
        avg_d = (d1 + d2 + d3) / 3
    else:
        avg_d = 0
    alpha = calculate_alpha(avg_d)

    DrawRectangle(X1=0, Y1=0, X2=0.1, Y2=0.1, Color=(255, 255, 255), Thickness=1)

    dpg.render_dearpygui_frame()