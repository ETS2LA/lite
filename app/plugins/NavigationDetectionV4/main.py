from plugins.SDKController.main import SCSController as SCSController
from plugins.TruckSimAPI.main import scsTelemetry as SCSTelemetry
import plugins.ScreenCapture.main as ScreenCapture
from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import src.console as console
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

global Enabled
Enabled = True

def Initialize():
    global EnableKey
    global EnableKeyPressed
    global LastEnableKeyPressed
    global LastScreenCaptureCheck

    global SteeringOffset
    global SteeringSmoothness
    global SteeringSensitivity
    global SteeringMaximum

    global SDKController
    global TruckSimAPI

    EnableKey = settings.Get("Steering", "EnableKey", "n")
    EnableKeyPressed = False
    LastEnableKeyPressed = False
    LastScreenCaptureCheck = 0

    SteeringOffset = 0
    SteeringSmoothness = 3
    SteeringSensitivity = 0.5
    SteeringMaximum = 1

    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()

    ScreenCapture.Initialize()


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


def plugin():
    CurrentTime = time.time()

    global Enabled
    global EnableKey
    global EnableKeyPressed
    global LastEnableKeyPressed
    global LastScreenCaptureCheck

    global SDKController
    global TruckSimAPI

    data = {}
    data["api"] = TruckSimAPI.update()
    frame = ScreenCapture.plugin(imgtype="cropped")

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

    EnableKeyPressed = keyboard.is_pressed(EnableKey)
    if EnableKeyPressed == False and LastEnableKeyPressed == True:
        Enabled = not Enabled
    LastEnableKeyPressed = EnableKeyPressed



    Steering = 0



    SDKController.steering = float(Steering)

    text, fontscale, thickness, text_width_enabled, text_height_enabled = GetTextSize(text="Enabled" if Enabled else "Disabled", text_width=width/1.1, max_text_height=height/11)
    cv2.putText(frame, text, (5, 5 + text_height_enabled), cv2.FONT_HERSHEY_SIMPLEX, fontscale, (0, 255, 0) if Enabled else (0, 0, 255), thickness, cv2.LINE_AA)

    currentDesired = Steering
    actualSteering = -data["api"]["truckFloat"]["gameSteer"]

    divider = 5
    cv2.line(frame, (int(width/divider), int(height - height/10)), (int(width/divider*(divider-1)), int(height - height/10)), (100, 100, 100), 6, cv2.LINE_AA)
    cv2.line(frame, (int(width/2), int(height - height/10)), (int(width/2 + actualSteering * (width/2 - width/divider)), int(height - height/10)), (0, 255, 100), 6, cv2.LINE_AA)
    cv2.line(frame, (int(width/2), int(height - height/10)), (int(width/2 + (currentDesired if abs(currentDesired) < 1 else (1 if currentDesired > 0 else -1)) * (width/2 - width/divider)), int(height - height/10)), (0, 100, 255), 2, cv2.LINE_AA)

    try:
        _, _, _, _ = cv2.getWindowImageRect("NavigationDetectionV4")
    except:
        cv2.namedWindow("NavigationDetectionV4", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("NavigationDetectionV4", cv2.WND_PROP_TOPMOST, 1)

        if variables.OS == "nt":
            hwnd = win32gui.FindWindow(None, "NavigationDetectionV4")
            windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(c_int(0x000000)), sizeof(c_int))
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(None, f"{variables.PATH}app/assets/favicon.ico", win32con.IMAGE_ICON, 0, 0, icon_flags)
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
            win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

    cv2.imshow("NavigationDetectionV4", frame)
    cv2.waitKey(1)

    return