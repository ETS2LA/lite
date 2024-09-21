from plugins.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from plugins.SDKController.main import SCSController
import plugins.ScreenCapture.main as ScreenCapture
from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import src.console as console
import src.pytorch as pytorch
import numpy as np
import traceback
import keyboard
import time
import cv2
import mss
import os

if variables.OS == "nt":
    import win32gui, win32con
    from ctypes import windll, byref, sizeof, c_int

global enabled
enabled = True

def Initialize():
    global enable_key
    global enable_key_pressed
    global last_enable_key_pressed
    global LastScreenCaptureCheck

    global MapTopLeft
    global MapBottomRight

    global SteeringOffset
    global SteeringSmoothness
    global SteeringSensitivity
    global SteeringMaximum

    global indicator_last_left
    global indicator_last_right
    global indicator_left_wait_for_response
    global indicator_right_wait_for_response
    global indicator_left_response_timer
    global indicator_right_response_timer

    global SDKController
    global TruckSimAPI

    enable_key = settings.Get("Steering", "EnableKey", "n")
    enable_key_pressed = False
    last_enable_key_pressed = False
    LastScreenCaptureCheck = 0

    pytorch.Initialize()
    pytorch.LoadAIModel()

    variables.POPUP = ["Loading...", 0, 0.5]

    MapTopLeft = settings.Get("NavigationDetectionAI", "MapTopLeft", "unset")
    MapBottomRight = settings.Get("NavigationDetectionAI", "MapBottomRight", "unset")

    if MapTopLeft == "unset":
        MapTopLeft = None
    if MapBottomRight == "unset":
        MapBottomRight = None

    SteeringOffset = settings.Get("Steering", "Offset", 0)
    SteeringSmoothness = settings.Get("Steering", "Smoothness", 3)
    SteeringSensitivity = settings.Get("Steering", "Sensitivity", 0.5)
    SteeringMaximum = settings.Get("Steering", "Maximum", 1)

    indicator_last_left = False
    indicator_last_right = False
    indicator_left_wait_for_response = False
    indicator_right_wait_for_response = False
    indicator_left_response_timer = 0
    indicator_right_response_timer = 0

    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()

    ScreenCapture.Initialize()


def UpdateSettings():
    global SteeringOffset
    global SteeringSmoothness
    global SteeringSensitivity
    global SteeringMaximum

    SteeringOffset = settings.Get("Steering", "Offset", 0)
    SteeringSmoothness = settings.Get("Steering", "Smoothness", 3)
    SteeringSensitivity = settings.Get("Steering", "Sensitivity", 0.5)
    SteeringMaximum = settings.Get("Steering", "Maximum", 1)


def get_text_size(text="NONE", text_width=100, max_text_height=100):
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


def GetRouteAdvisorPosition():
    x1, y1, x2, y2 = GetGamePosition()
    distance_from_right = 21
    distance_from_bottom = 100
    width = 420
    height = 219
    scale = (y2 - y1) / 1080
    x = x1 + (x2 - x1) - (distance_from_right * scale + width * scale)
    y = y1 + (y2 - y1) - (distance_from_bottom * scale + height * scale)
    map_topleft = (round(x), round(y))
    x = x1 + (x2 - x1) - (distance_from_right * scale)
    y = y1 + (y2 - y1) - (distance_from_bottom * scale)
    map_bottomright = (round(x), round(y))
    x = map_bottomright[0] - (map_bottomright[0] - map_topleft[0]) * 0.57
    y = map_bottomright[1] - (map_bottomright[1] - map_topleft[1]) * 0.575
    arrow_topleft = (round(x), round(y))
    x = map_bottomright[0] - (map_bottomright[0] - map_topleft[0]) * 0.43
    y = map_bottomright[1] - (map_bottomright[1] - map_topleft[1]) * 0.39
    arrow_bottomright = (round(x), round(y))
    return map_topleft, map_bottomright, arrow_topleft, arrow_bottomright


def preprocess_image(image):
    image = np.array(image)
    image = cv2.resize(image, (pytorch.IMG_WIDTH, pytorch.IMG_HEIGHT))
    image = np.array(image, dtype=np.float32) / 255.0
    transform = pytorch.transforms.Compose([
        pytorch.transforms.ToTensor(),
    ])
    return transform(image).unsqueeze(0).to(pytorch.DEVICE)


def plugin():
    CurrentTime = time.time()

    global enabled
    global enable_key
    global enable_key_pressed
    global last_enable_key_pressed
    global LastScreenCaptureCheck

    global MapTopLeft
    global MapBottomRight

    global indicator_last_left
    global indicator_last_right
    global indicator_left_wait_for_response
    global indicator_right_wait_for_response
    global indicator_left_response_timer
    global indicator_right_response_timer

    global SDKController
    global TruckSimAPI

    data = {}
    data["api"] = TruckSimAPI.update()
    frame = ScreenCapture.plugin(ImageType="cropped")

    try:
        try:
            while pytorch.AIModelUpdateThread.is_alive(): return 0
            while pytorch.AIModelLoadThread.is_alive(): return 0
        except:
            return 0

        if type(frame) == type(None):
            return

        if LastScreenCaptureCheck + 0.5 < CurrentTime:
            map_topleft, map_bottomright, arrow_topleft, arrow_bottomright = GetRouteAdvisorPosition()
            screen_x, screen_y, _, _ = GetScreenDimensions(GetScreenIndex((map_topleft[0] + map_bottomright[0]) / 2, (map_topleft[1] + map_bottomright[1]) / 2))
            if ScreenCapture.monitor_x1 != map_topleft[0] - screen_x or ScreenCapture.monitor_y1 != map_topleft[1] - screen_y or ScreenCapture.monitor_x2 != map_bottomright[0] - screen_x or ScreenCapture.monitor_y2 != map_bottomright[1] - screen_y:
                ScreenIndex = GetScreenIndex((map_topleft[0] + map_bottomright[0]) / 2, (map_topleft[1] + map_bottomright[1]) / 2)
                if ScreenCapture.display != ScreenIndex - 1:
                    settings.Set("ScreenCapture", "Display", ScreenIndex - 1)
                    if ScreenCapture.cam_library == "WindowsCapture":
                        ScreenCapture.StopWindowsCapture = True
                        while ScreenCapture.StopWindowsCapture == True:
                            time.sleep(0.01)
                    ScreenCapture.Initialize()
                ScreenCapture.monitor_x1, ScreenCapture.monitor_y1, ScreenCapture.monitor_x2, ScreenCapture.monitor_y2 = ValidateCaptureArea(ScreenIndex, map_topleft[0] - screen_x, map_topleft[1] - screen_y, map_bottomright[0] - screen_x, map_bottomright[1] - screen_y)
            LastScreenCaptureCheck = CurrentTime

        width = frame.shape[1]
        height = frame.shape[0]

        if width <= 0 or height <= 0:
            return

        enable_key_pressed = keyboard.is_pressed(enable_key)
        if enable_key_pressed == False and last_enable_key_pressed == True:
            enabled = not enabled
        last_enable_key_pressed = enable_key_pressed

        cv2.rectangle(frame, (0, 0), (round(frame.shape[1]/6), round(frame.shape[0]/3)), (0, 0, 0), -1)
        cv2.rectangle(frame, (frame.shape[1] ,0), (round(frame.shape[1]-frame.shape[1]/6), round(frame.shape[0]/3)), (0, 0, 0), -1)
        lower_red = np.array([0, 0, 160])
        upper_red = np.array([110, 110, 255])
        mask = cv2.inRange(frame, lower_red, upper_red)
        frame_with_mask = cv2.bitwise_and(frame, frame, mask=mask)
        frame = cv2.cvtColor(frame_with_mask, cv2.COLOR_BGR2GRAY)

        if cv2.countNonZero(frame) / (frame.shape[0] * frame.shape[1]) > 0.03:
            lane_detected = True
        else:
            lane_detected = False

        try:
            AIFrame = preprocess_image(mask)
            output = [[0] * pytorch.MODEL_OUTPUTS]
        except:
            pytorch.GetAIModelProperties()
            if pytorch.IMG_WIDTH == None or pytorch.IMG_HEIGHT == None or pytorch.MODEL_OUTPUTS == None:
                global TorchAvailable
                TorchAvailable = False
                console.RestoreConsole()
                return
            AIFrame = preprocess_image(mask)
            output = [[0] * pytorch.MODEL_OUTPUTS]

        if enabled == True:
            if pytorch.ModelLoaded == True:
                with pytorch.torch.no_grad():
                    output = pytorch.Model(AIFrame)
                    output = output.tolist()

        steering = float(output[0][0]) / -30
        left_indicator = bool(float(output[0][1]) > 0.15)
        right_indicator = bool(float(output[0][2]) > 0.15)

        if lane_detected == False:
            steering = 0
            left_indicator = False
            right_indicator = False

        try:
            indicator_left = data["api"]["truckBool"]["blinkerLeftActive"]
            indicator_right = data["api"]["truckBool"]["blinkerRightActive"]
        except:
            indicator_left = False
            indicator_right = False

        if enabled == True:
            if left_indicator != indicator_left and indicator_left_wait_for_response == False:
                SDKController.lblinker = not SDKController.lblinker
                indicator_left_wait_for_response = True
                indicator_left_response_timer = CurrentTime
            if right_indicator != indicator_right and indicator_right_wait_for_response == False:
                SDKController.rblinker = not SDKController.rblinker
                indicator_right_wait_for_response = True
                indicator_right_response_timer = CurrentTime

            if indicator_left != indicator_last_left:
                indicator_left_wait_for_response = False
            if indicator_right != indicator_last_right:
                indicator_right_wait_for_response = False
            if CurrentTime - 1 > indicator_left_response_timer:
                indicator_left_wait_for_response = False
            if CurrentTime - 1 > indicator_right_response_timer:
                indicator_right_wait_for_response = False
        indicator_last_left = left_indicator
        indicator_last_right = right_indicator

        SDKController.steering = steering * 0.65

        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        text, fontscale, thickness, text_width_enabled, text_height_enabled = get_text_size(text="Enabled" if enabled else "Disabled", text_width=width/1.1, max_text_height=height/11)
        cv2.putText(frame, text, (5, 5 + text_height_enabled), cv2.FONT_HERSHEY_SIMPLEX, fontscale, (0, 255, 0) if enabled else (0, 0, 255), thickness, cv2.LINE_AA)

        currentDesired = steering
        actualSteering = -data["api"]["truckFloat"]["gameSteer"]

        divider = 5
        cv2.line(frame, (int(width/divider), int(height - height/10)), (int(width/divider*(divider-1)), int(height - height/10)), (100, 100, 100), 6, cv2.LINE_AA)
        cv2.line(frame, (int(width/2), int(height - height/10)), (int(width/2 + actualSteering * (width/2 - width/divider)), int(height - height/10)), (0, 255, 100), 6, cv2.LINE_AA)
        cv2.line(frame, (int(width/2), int(height - height/10)), (int(width/2 + (currentDesired if abs(currentDesired) < 1 else (1 if currentDesired > 0 else -1)) * (width/2 - width/divider)), int(height - height/10)), (0, 100, 255), 2, cv2.LINE_AA)

        try:
            _, _, _, _ = cv2.getWindowImageRect("Lane Assist")
        except:
            cv2.namedWindow('Lane Assist', cv2.WINDOW_NORMAL)
            cv2.setWindowProperty('Lane Assist', cv2.WND_PROP_TOPMOST, 1)

            if variables.OS == "nt":
                hwnd = win32gui.FindWindow(None, "Lane Assist")
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(c_int(0x000000)), sizeof(c_int))
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                hicon = win32gui.LoadImage(None, f"{variables.PATH}app/assets/favicon.ico", win32con.IMAGE_ICON, 0, 0, icon_flags)
                win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
                win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

        cv2.imshow("Lane Assist", frame)
        cv2.waitKey(1)

    except Exception as e:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Running AI Error.", str(exc))
        console.RestoreConsole()
        print("\033[91m" + f"NavigationDetection - Running AI Error: " + "\033[0m" + str(e))

    return