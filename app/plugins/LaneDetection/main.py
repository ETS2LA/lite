from plugins.SDKController.main import SCSController as SCSController
from plugins.TruckSimAPI.main import scsTelemetry as SCSTelemetry
import plugins.ScreenCapture.main as ScreenCapture
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


from torchvision import transforms
import torch


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


sct = mss.mss()
def GetScreenDimensions(monitor=1):
    global screen_x, screen_y, screen_width, screen_height
    monitor = sct.monitors[monitor]
    screen_x = monitor["left"]
    screen_y = monitor["top"]
    screen_width = monitor["width"]
    screen_height = monitor["height"]
    return screen_x, screen_y, screen_width, screen_height
GetScreenDimensions()


def GetScreenIndex(x, y):
    with mss.mss() as sct:
        monitors = sct.monitors
    closest_screen_index = None
    closest_distance = float('inf')
    for i, monitor in enumerate(monitors[1:]):
        center_x = (monitor['left'] + monitor['left'] + monitor['width']) // 2
        center_y = (monitor['top'] + monitor['top'] + monitor['height']) // 2
        distance = ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5
        if distance < closest_distance:
            closest_screen_index = i + 1
            closest_distance = distance
    return closest_screen_index


def ValidateCaptureArea(monitor, x1, y1, x2, y2):
    monitor = sct.monitors[monitor]
    width, height = monitor["width"], monitor["height"]
    x1 = max(0, min(width - 1, x1))
    x2 = max(0, min(width - 1, x2))
    y1 = max(0, min(height - 1, y1))
    y2 = max(0, min(height - 1, y2))
    if x1 == x2:
        if x1 == 0:
            x2 = width - 1
        else:
            x1 = 0
    if y1 == y2:
        if y1 == 0:
            y2 = height - 1
        else:
            y1 = 0
    return x1, y1, x2, y2


def GetGamePosition():
    global LastGetGamePosition
    if variables.OS == "nt":
        if LastGetGamePosition[0] + 1 < time.time():
            hwnd = None
            top_windows = []
            window = LastGetGamePosition[1], LastGetGamePosition[2], LastGetGamePosition[3], LastGetGamePosition[4]
            win32gui.EnumWindows(lambda hwnd, top_windows: top_windows.append((hwnd, win32gui.GetWindowText(hwnd))), top_windows)
            for hwnd, window_text in top_windows:
                if "Truck Simulator" in window_text and "Discord" not in window_text:
                    rect = win32gui.GetClientRect(hwnd)
                    tl = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
                    br = win32gui.ClientToScreen(hwnd, (rect[2], rect[3]))
                    window = (tl[0], tl[1], br[0] - tl[0], br[1] - tl[1])
                    break
            LastGetGamePosition = time.time(), window[0], window[1], window[0] + window[2], window[1] + window[3]
            return window[0], window[1], window[0] + window[2], window[1] + window[3]
        else:
            return LastGetGamePosition[1], LastGetGamePosition[2], LastGetGamePosition[3], LastGetGamePosition[4]
    else:
        return screen_x, screen_y, screen_x + screen_width, screen_y + screen_height
LastGetGamePosition = 0, screen_x, screen_y, screen_width, screen_height


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


def plugin():
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
    frame = ScreenCapture.plugin(ImageType="cropped")

    if type(frame) == type(None):
        return

    if LastScreenCaptureCheck + 0.5 < CurrentTime:
        game_x1, game_y1, game_x2, game_y2 = GetGamePosition()
        if ScreenCapture.monitor_x1 != game_x1 or ScreenCapture.monitor_y1 != game_y1 or ScreenCapture.monitor_x2 != game_x2 or ScreenCapture.monitor_y2 != game_y2:
            ScreenIndex = GetScreenIndex((game_x1 + game_x2) / 2, (game_y1 + game_y2) / 2)
            if ScreenCapture.display != ScreenIndex - 1:
                settings.Set("ScreenCapture", "Display", ScreenIndex - 1)
                if ScreenCapture.cam_library == "WindowsCapture":
                    ScreenCapture.StopWindowsCapture = True
                    while ScreenCapture.StopWindowsCapture == True:
                        time.sleep(0.01)
                ScreenCapture.Initialize()
            ScreenCapture.monitor_x1, ScreenCapture.monitor_y1, ScreenCapture.monitor_x2, ScreenCapture.monitor_y2 = ValidateCaptureArea(ScreenIndex, game_x1, game_y1, game_x2, game_y2)
        LastScreenCaptureCheck = CurrentTime

    width = frame.shape[1]
    height = frame.shape[0]

    if width <= 0 or height <= 0:
        return


    
    try:
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


    offset_x = 1
    offset_y = 0.1
    offset_z = 0.35

    point_x = head_x + offset_x * math.sin(truck_rotation_radians_x) - offset_z * math.cos(truck_rotation_radians_x)
    point_y = head_y + offset_y
    point_z = head_z - offset_x * math.cos(truck_rotation_radians_x) - offset_z * math.sin(truck_rotation_radians_x)

    x1, y1, d1 = ConvertToScreenCoordinate(point_x, point_y, point_z)
    if x1 == None or y1 == None:
        all_valid = False
    else:
        top_left = x1, y1


    offset_x = 1
    offset_y = 0.1
    offset_z = -0.35

    point_x = head_x + offset_x * math.sin(truck_rotation_radians_x) - offset_z * math.cos(truck_rotation_radians_x)
    point_y = head_y + offset_y
    point_z = head_z - offset_x * math.cos(truck_rotation_radians_x) - offset_z * math.sin(truck_rotation_radians_x)

    x1, y1, d1 = ConvertToScreenCoordinate(point_x, point_y, point_z)
    if x1 == None or y1 == None:
        all_valid = False
    else:
        top_right = x1, y1


    offset_x = 1
    offset_y = -0.3
    offset_z = 0.35

    point_x = head_x + offset_x * math.sin(truck_rotation_radians_x) - offset_z * math.cos(truck_rotation_radians_x)
    point_y = head_y + offset_y
    point_z = head_z - offset_x * math.cos(truck_rotation_radians_x) - offset_z * math.sin(truck_rotation_radians_x)

    x1, y1, d1 = ConvertToScreenCoordinate(point_x, point_y, point_z)
    if x1 == None or y1 == None:
        all_valid = False
    else:
        bottom_left = x1, y1


    offset_x = 1
    offset_y = -0.3
    offset_z = -0.35

    point_x = head_x + offset_x * math.sin(truck_rotation_radians_x) - offset_z * math.cos(truck_rotation_radians_x)
    point_y = head_y + offset_y 
    point_z = head_z - offset_x * math.cos(truck_rotation_radians_x) - offset_z * math.sin(truck_rotation_radians_x)

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

    steering = data["api"]["truckFloat"]["gameSteer"]
    throttle = data["api"]["truckFloat"]["gameThrottle"]
    brake = data["api"]["truckFloat"]["gameBrake"]
    speed = data["api"]["truckFloat"]["speed"]
    speed_limit = data["api"]["truckFloat"]["speedLimit"]
    truck_pitch = data["api"]["truckPlacement"]["rotationY"]


    if LastDataTime + 0.5 < CurrentTime and data["api"]["pause"] == False:
        if os.path.exists(f"{variables.PATH}DataCaptures") == False:
            os.mkdir(f"{variables.PATH}DataCaptures")
        LastDataTime = CurrentTime
        name = str(len([name for name in os.listdir(f"{variables.PATH}DataCaptures") if name.endswith(".png")]))
        cv2.imwrite(f"{variables.PATH}DataCaptures/{name}.png", frame)
        data = {"Steering": steering, "Speed": speed, "SpeedLimit": speed_limit, "TruckPitch": truck_pitch, "Throttle": throttle, "Brake": brake}
        with open(f"{variables.PATH}DataCaptures/{name}.txt", "w") as f:
            f.write(str(data))


    #frame = cv2.resize(frame, (200, 200))
    #image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #image = np.array(image, dtype=np.float32) / 255.0
    #transform = transforms.Compose([
    #    transforms.ToTensor(),
    #])
    #image = transform(image).unsqueeze(0)
    #with torch.no_grad():
    #    prediction = model(image.to(device))

    #prediction = prediction.squeeze(0).permute(1, 2, 0).cpu().numpy()

    #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    #prediction_overlay = cv2.cvtColor(prediction, cv2.COLOR_GRAY2BGRA)

    #prediction_overlay[:, :, 2] = 0
    #prediction_overlay = prediction_overlay.astype(np.uint8) * 255

    #frame = cv2.addWeighted(frame, 1, prediction_overlay, 0.5, 0)

    #non_black_pixels = np.where(prediction_overlay[:, :, 0] != 0)
    #if len(non_black_pixels[0]) > 0:
    #    x_center = int(np.mean(non_black_pixels[1]))
    #else:
    #    x_center = frame.shape[1] / 2
    #cv2.line(frame, (round(x_center), 0), (round(x_center), height), (0, 255, 0), 1)



    #image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #avg_color = 70
    #mean_color = np.mean(image)
    #if mean_color != avg_color:
    #    scaling_factor = avg_color / mean_color
    #    image = cv2.multiply(image, scaling_factor)
    #    image = np.clip(image, 0, 255).astype(np.uint8)
    #image = cv2.addWeighted(image, 4, cv2.GaussianBlur(image, (0, 0), 20), -4, 0)

    ## only keep the 30 larges blobs
    #image = cv2.medianBlur(image, 5)

    #image = cv2.Canny(image, 50, 200)

    #lines = cv2.HoughLines(image, 1, np.pi/180, 200)
    #if lines is None:
    #    return
    #for r_theta in lines:
    #    arr = np.array(r_theta[0], dtype=np.float64)
    #    r, theta = arr
    #    a = np.cos(theta)
    #    b = np.sin(theta)
    #    x0 = a*r
    #    y0 = b*r
    #    x1 = int(x0 + 1000*(-b))
    #    y1 = int(y0 + 1000*(a))
    #    x2 = int(x0 - 1000*(-b))
    #    y2 = int(y0 - 1000*(a))
    #    cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)



    #Steering = 0
    #SDKController.steering = float(Steering)

    try:
        _, _, _, _ = cv2.getWindowImageRect("LaneDetection")
    except:
        cv2.namedWindow("LaneDetection", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("LaneDetection", cv2.WND_PROP_TOPMOST, 1)

        if variables.OS == "nt":
            hwnd = win32gui.FindWindow(None, "LaneDetection")
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(c_int(0x000000)), sizeof(c_int))
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(None, f"{variables.PATH}app/assets/favicon.ico", win32con.IMAGE_ICON, 0, 0, icon_flags)
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

    cv2.imshow("LaneDetection", frame)
    cv2.waitKey(1)

    return