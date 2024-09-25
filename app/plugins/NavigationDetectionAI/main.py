from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from modules.SDKController.main import SCSController
import modules.ScreenCapture.main as ScreenCapture
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

if variables.OS == "nt":
    import win32gui, win32con
    from ctypes import windll, byref, sizeof, c_int

global enabled
enabled = True
sct = mss.mss()

def Initialize():
    global enable_key
    global enable_key_pressed
    global last_enable_key_pressed
    global LastScreenCaptureCheck
    global SteeringHistory

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
    SteeringHistory = []

    pytorch.Initialize(ModelOwner="Glas42", ModelName="NavigationDetectionAI")
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





def preprocess_image(image):
    image = np.array(image)
    image = cv2.resize(image, (pytorch.IMG_WIDTH, pytorch.IMG_HEIGHT))
    image = np.array(image, dtype=np.float32) / 255.0
    transform = pytorch.transforms.Compose([
        pytorch.transforms.ToTensor(),
    ])
    return transform(image).unsqueeze(0).to(pytorch.DEVICE)


def Run(data):
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

    data["api"] = TruckSimAPI.update()
    try:
        frame = ScreenCapture.Capture(ImageType="cropped")
    except:
        SendCrashReport("ScreenCapture - Error in function plugin.", str(traceback.format_exc()))
        exit()

    try:
        try:
            while pytorch.AIModelUpdateThread.is_alive(): return
            while pytorch.AIModelLoadThread.is_alive(): return
        except:
            return

        if type(frame) == type(None):
            return

        if LastScreenCaptureCheck + 0.5 < CurrentTime:
            MapTopLeft, MapBottomRight, ArrowTopLeft, ArrowBottomRight = ScreenCapture.GetRouteAdvisorPosition()
            ScreenX, ScreenY, _, _ = ScreenCapture.GetScreenDimensions(ScreenCapture.GetScreenIndex((MapTopLeft[0] + MapBottomRight[0]) / 2, (MapTopLeft[1] + MapBottomRight[1]) / 2))
            if ScreenCapture.MonitorX1 != MapTopLeft[0] - ScreenX or ScreenCapture.MonitorY1 != MapTopLeft[1] - ScreenY or ScreenCapture.MonitorX2 != MapBottomRight[0] - ScreenX or ScreenCapture.MonitorY2 != MapBottomRight[1] - ScreenY:
                ScreenIndex = ScreenCapture.GetScreenIndex((MapTopLeft[0] + MapBottomRight[0]) / 2, (MapTopLeft[1] + MapBottomRight[1]) / 2)
                if ScreenCapture.Display != ScreenIndex - 1:
                    if ScreenCapture.CaptureLibrary == "WindowsCapture":
                        ScreenCapture.StopWindowsCapture = True
                        while ScreenCapture.StopWindowsCapture == True:
                            time.sleep(0.01)
                    ScreenCapture.Initialize()
                ScreenCapture.MonitorX1, ScreenCapture.MonitorY1, ScreenCapture.MonitorX2, ScreenCapture.MonitorY2 = ScreenCapture.ValidateCaptureArea(ScreenIndex, MapTopLeft[0] - ScreenX, MapTopLeft[1] - ScreenY, MapBottomRight[0] - ScreenX, MapBottomRight[1] - ScreenY)
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

        Steering = steering * 0.65

        SteeringHistory.append((Steering, CurrentTime))
        SteeringHistory.sort(key=lambda x: x[1])
        while CurrentTime - SteeringHistory[0][1] > 0.2:
            SteeringHistory.pop(0)
        Steering = sum(x[0] for x in SteeringHistory) / len(SteeringHistory)

        SDKController.steering = Steering

        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        text, fontscale, thickness, text_width_enabled, text_height_enabled = GetTextSize(text="Enabled" if enabled else "Disabled", text_width=width/1.1, max_text_height=height/11)
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

    except:
        SendCrashReport("NavigationDetectionAI - Running AI Error.", str(traceback.format_exc()))

    return