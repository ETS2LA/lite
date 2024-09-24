from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from modules.SDKController.main import SCSController
import modules.ScreenCapture.main as ScreenCapture
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

    global LastDataTime
    LastDataTime = 0

    global SteeringHistory
    SteeringHistory = []

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


def ConvertToScreenCoordinate(x:float, y:float, z:float):

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

    fov_rad = math.radians(80)
    window_distance = (height * (4 / 3) / 2) / math.tan(fov_rad / 2)

    screen_x = (final_x / final_z) * window_distance + width / 2
    screen_y = (final_y / final_z) * window_distance + height / 2

    screen_x = width - screen_x

    distance = math.sqrt((rel_x ** 2) + (rel_y ** 2) + (rel_z ** 2))

    return screen_x, screen_y, distance


def Run(data):
    CurrentTime = time.time()

    global LastScreenCaptureCheck
    global SDKController
    global TruckSimAPI

    global width
    global height

    global head_x
    global head_y
    global head_z
    global head_rotation_degrees_x
    global head_rotation_degrees_y
    global head_rotation_degrees_z

    global LastDataTime

    data = {}
    data["api"] = TruckSimAPI.update()
    frame = ScreenCapture.Capture(ImageType="cropped")

    if type(frame) == type(None):
        return

    width = frame.shape[1]
    height = frame.shape[0]

    if width <= 0 or height <= 0:
        return

    if LastScreenCaptureCheck + 0.5 < CurrentTime:
        WindowX1, WindowY1, WindowX2, WindowY2 = ScreenCapture.GetWindowPosition(Name="Truck Simulator", Blacklist=["Discord"])
        if ScreenCapture.MonitorX1 != WindowX1 or ScreenCapture.MonitorY1 != WindowY1 or ScreenCapture.MonitorX2!= WindowX2 or ScreenCapture.MonitorY2 != WindowY2:
            ScreenIndex = ScreenCapture.GetScreenIndex((WindowX1 + WindowX2) / 2, (WindowY1 + WindowY2) / 2)
            if ScreenCapture.Display != ScreenIndex - 1:
                settings.Set("ScreenCapture", "Display", ScreenIndex - 1)
                if ScreenCapture.CaptureLibrary == "WindowsCapture":
                    ScreenCapture.StopWindowsCapture = True
                    while ScreenCapture.StopWindowsCapture == True:
                        time.sleep(0.01)
                ScreenCapture.Initialize()
            ScreenCapture.MonitorX1, ScreenCapture.MonitorY1, ScreenCapture.MonitorX2, ScreenCapture.MonitorY2 = ScreenCapture.ValidateCaptureArea(ScreenIndex, WindowX1, WindowY1, WindowX2, WindowY2)
        LastScreenCaptureCheck = CurrentTime

    
    try:
        truck_x = data["api"]["truckPlacement"]["coordinateX"]
        truck_y = data["api"]["truckPlacement"]["coordinateY"]
        truck_z = data["api"]["truckPlacement"]["coordinateZ"]
        truck_rotation_x = data["api"]["truckPlacement"]["rotationX"]
        truck_rotation_y = 0
        truck_rotation_z = 0

        WheelRadii = data["api"]["configFloat"]["truckWheelRadius"]
        WheelYs = data["api"]["configVector"]["truckWheelPositionY"]
        if len(WheelRadii) >= 4:
            AverageWheelRadius = WheelRadii[0] + WheelRadii[1] + WheelRadii[2] + WheelRadii[3]
        else:
            AverageWheelRadius = 0

        cabin_offset_x = data["api"]["headPlacement"]["cabinOffsetX"] + data["api"]["configVector"]["cabinPositionX"]
        cabin_offset_y = data["api"]["headPlacement"]["cabinOffsetY"] + data["api"]["configVector"]["cabinPositionY"]
        cabin_offset_z = data["api"]["headPlacement"]["cabinOffsetZ"] + data["api"]["configVector"]["cabinPositionZ"]
        cabin_offset_rotation_x = data["api"]["headPlacement"]["cabinOffsetrotationX"]
        cabin_offset_rotation_y = data["api"]["headPlacement"]["cabinOffsetrotationY"]
        cabin_offset_rotation_z = 0

        head_offset_x = data["api"]["headPlacement"]["headOffsetX"] + data["api"]["configVector"]["headPositionX"] + cabin_offset_x
        head_offset_y = data["api"]["headPlacement"]["headOffsetY"] + data["api"]["configVector"]["headPositionY"] + cabin_offset_y
        head_offset_z = data["api"]["headPlacement"]["headOffsetZ"] + data["api"]["configVector"]["headPositionZ"] + cabin_offset_z
        head_offset_rotation_x = data["api"]["headPlacement"]["headOffsetrotationX"]
        head_offset_rotation_y = data["api"]["headPlacement"]["headOffsetrotationY"]
        head_offset_rotation_z = 0
        
        truck_rotation_degrees_x = truck_rotation_x * 360
        truck_rotation_radians_x = -math.radians(truck_rotation_degrees_x)

        head_rotation_degrees_x = (truck_rotation_x + cabin_offset_rotation_x + head_offset_rotation_x) * 360
        while head_rotation_degrees_x > 360:
            head_rotation_degrees_x = head_rotation_degrees_x - 360

        head_rotation_degrees_y = (-truck_rotation_y + cabin_offset_rotation_y + head_offset_rotation_y) * 360

        head_rotation_degrees_z = (truck_rotation_z + cabin_offset_rotation_z + head_offset_rotation_z) * 360

        point_x = head_offset_x
        point_y = head_offset_y
        point_z = head_offset_z
        head_x = point_x * math.cos(truck_rotation_radians_x) - point_z * math.sin(truck_rotation_radians_x) + truck_x
        head_y = point_y * math.cos(math.radians(head_rotation_degrees_y)) - point_z * math.sin(math.radians(head_rotation_degrees_y)) + truck_y
        head_z = point_x * math.sin(truck_rotation_radians_x) + point_z * math.cos(truck_rotation_radians_x) + truck_z

    except:

        truck_x = 0
        truck_y = 0
        truck_z = 0
        truck_rotation_x = 0
        truck_rotation_y = 0
        truck_rotation_z = 0

        cabin_offset_x = 0
        cabin_offset_y = 0
        cabin_offset_z = 0
        cabin_offset_rotation_x = 0
        cabin_offset_rotation_y = 0
        cabin_offset_rotation_z = 0

        head_offset_x = 0
        head_offset_y = 0
        head_offset_z = 0
        head_offset_rotation_x = 0
        head_offset_rotation_y = 0
        head_offset_rotation_z = 0

        truck_rotation_degrees_x = 0
        truck_rotation_radians_x = 0

        head_rotation_degrees_x = 0
        head_rotation_degrees_y = 0
        head_rotation_degrees_z = 0

        head_x = 0
        head_y = 0
        head_z = 0


    all_valid = True


    offset_x = 50
    offset_z = 4

    point_x = truck_x + offset_x * math.sin(truck_rotation_radians_x) - offset_z * math.cos(truck_rotation_radians_x)
    point_y = truck_y
    point_z = truck_z - offset_x * math.cos(truck_rotation_radians_x) - offset_z * math.sin(truck_rotation_radians_x)

    x1, y1, d1 = ConvertToScreenCoordinate(point_x, point_y, point_z)
    if x1 == None or y1 == None:
        all_valid = False
    else:
        top_left = x1, y1


    offset_x = 50
    offset_z = -4

    point_x = truck_x + offset_x * math.sin(truck_rotation_radians_x) - offset_z * math.cos(truck_rotation_radians_x)
    point_y = truck_y
    point_z = truck_z - offset_x * math.cos(truck_rotation_radians_x) - offset_z * math.sin(truck_rotation_radians_x)

    x1, y1, d1 = ConvertToScreenCoordinate(point_x, point_y, point_z)
    if x1 == None or y1 == None:
        all_valid = False
    else:
        top_right = x1, y1


    offset_x = 12.5
    offset_z = 4

    point_x = truck_x + offset_x * math.sin(truck_rotation_radians_x) - offset_z * math.cos(truck_rotation_radians_x)
    point_y = truck_y
    point_z = truck_z - offset_x * math.cos(truck_rotation_radians_x) - offset_z * math.sin(truck_rotation_radians_x)

    x1, y1, d1 = ConvertToScreenCoordinate(point_x, point_y, point_z)
    if x1 == None or y1 == None:
        all_valid = False
    else:
        bottom_left = x1, y1


    offset_x = 12.5
    offset_z = -4

    point_x = truck_x + offset_x * math.sin(truck_rotation_radians_x) - offset_z * math.cos(truck_rotation_radians_x)
    point_y = truck_y
    point_z = truck_z - offset_x * math.cos(truck_rotation_radians_x) - offset_z * math.sin(truck_rotation_radians_x)

    x1, y1, d1 = ConvertToScreenCoordinate(point_x, point_y, point_z)
    if x1 == None or y1 == None:
        all_valid = False
    else:
        bottom_right = x1, y1


    if all_valid:
        cropped_width = round(max(top_right[0] - top_left[0], bottom_right[0] - bottom_left[0]))
        cropped_height = round(max(bottom_left[1] - top_left[1], bottom_right[1] - top_right[1]))
        src_pts = np.float32([top_left, top_right, bottom_left, bottom_right])
        dst_pts = np.float32([[0, 0], [cropped_width, 0], [0, cropped_height], [cropped_width, cropped_height]])
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        frame = cv2.warpPerspective(frame, matrix, (cropped_width, cropped_height))


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

    try:
        _, _, _, _ = cv2.getWindowImageRect("AdaptiveCruiseControl")
    except:
        cv2.namedWindow("AdaptiveCruiseControl", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("AdaptiveCruiseControl", cv2.WND_PROP_TOPMOST, 1)

        if variables.OS == "nt":
            hwnd = win32gui.FindWindow(None, "AdaptiveCruiseControl")
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(c_int(0x000000)), sizeof(c_int))
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(None, f"{variables.PATH}app/assets/favicon.ico", win32con.IMAGE_ICON, 0, 0, icon_flags)
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

    cv2.imshow("AdaptiveCruiseControl", frame)
    cv2.waitKey(1)

    return