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
import os

if variables.OS == "nt":
    import win32gui, win32con
    from ctypes import windll, byref, sizeof, c_int

try:
    from torchvision import transforms
    from bs4 import BeautifulSoup
    import threading
    import requests
    import torch
    TorchAvailable = True
except:
    TorchAvailable = False
    exc = traceback.format_exc()
    SendCrashReport("NavigationDetection - PyTorch import error.", str(exc))
    print("\033[91m" + f"NavigationDetection - PyTorch import Error:\n" + "\033[0m" + str(exc))
    console.RestoreConsole()

global enabled
enabled = True

def Initialize():
    global enable_key
    global enable_key_pressed
    global last_enable_key_pressed

    global AIDevice
    global LoadAILabel
    global LoadAIProgress

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

    if TorchAvailable == True:
        LoadAIModel()
    else:
        print("NavigationDetectionAI not available due to missing dependencies.")
        console.RestoreConsole()
    AIDevice = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    LoadAILabel = "Loading..."
    LoadAIProgress = 0

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

    ScreenCapture.Initialize(settings.Get("ScreenCapture", "Display", 0))


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


def preprocess_image(image):
    image = np.array(image)
    image = cv2.resize(image, (IMG_WIDTH, IMG_HEIGHT))
    image = np.array(image, dtype=np.float32) / 255.0
    transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    return transform(image).unsqueeze(0).to(AIDevice)


def HandleCorruptedAIModel():
    DeleteAllAIModels()
    CheckForAIModelUpdates()
    while AIModelUpdateThread.is_alive(): time.sleep(0.1)
    time.sleep(0.5)
    if TorchAvailable == True:
        LoadAIModel()
    else:
        print("NavigationDetectionAI not available due to missing dependencies.")
        console.RestoreConsole()


def LoadAIModel():
    try:
        def LoadAIModelThread():
            try:
                global LoadAILabel
                global LoadAIProgress
                global AIModel
                global AIModelLoaded

                CheckForAIModelUpdates()
                while AIModelUpdateThread.is_alive(): time.sleep(0.1)

                if GetAIModelName() == "UNKNOWN":
                    return

                LoadAIProgress = 0
                LoadAILabel = "Loading the AI model..."

                print("\033[92m" + f"Loading the AI model..." + "\033[0m")

                GetAIModelProperties()

                ModelFileCorrupted = False

                try:
                    AIModel = torch.jit.load(os.path.join(f"{variables.PATH}plugins/NavigationDetectionAI/AIModel", GetAIModelName()), map_location=AIDevice)
                    AIModel.eval()
                except:
                    ModelFileCorrupted = True

                if ModelFileCorrupted == False:
                    print("\033[92m" + f"Successfully loaded the AI model!" + "\033[0m")
                    AIModelLoaded = True
                    LoadAIProgress = 100
                    LoadAILabel = "Successfully loaded the AI model!"
                else:
                    print("\033[91m" + f"Failed to load the AI model because the model file is corrupted." + "\033[0m")
                    AIModelLoaded = False
                    LoadAIProgress = 0
                    LoadAILabel = "ERROR! Your AI model file is corrupted!"
                    time.sleep(3)
                    HandleCorruptedAIModel()
            except Exception as e:
                exc = traceback.format_exc()
                SendCrashReport("NavigationDetection - Loading AI Error.", str(exc))
                console.RestoreConsole()
                print("\033[91m" + f"Failed to load the AI model." + "\033[0m")
                AIModelLoaded = False
                LoadAIProgress = 0
                LoadAILabel = "Failed to load the AI model!"

        global AIModelLoadThread
        AIModelLoadThread = threading.Thread(target=LoadAIModelThread)
        AIModelLoadThread.start()

    except Exception as ex:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function LoadAIModel.", str(exc))
        print(f"NavigationDetection - Error in function LoadAIModel: {ex}")
        console.RestoreConsole()
        print("\033[91m" + f"Failed to load the AI model." + "\033[0m")


def CheckForAIModelUpdates():
    try:
        def CheckForAIModelUpdatesThread():
            try:
                global LoadAILabel
                global LoadAIProgress

                try:
                    response = requests.get("https://huggingface.co/", timeout=3)
                    response = response.status_code
                except requests.exceptions.RequestException as ex:
                    response = None

                if response == 200:
                    LoadAIProgress = 0
                    LoadAILabel = "Checking for AI model updates..."

                    print("\033[92m" + f"Checking for AI model updates..." + "\033[0m")
                    if settings.Get("NavigationDetectionAI", "LastUpdateCheck", 0) + 600 > time.time():
                        if settings.Get("NavigationDetectionAI", "LatestModel", "unset") == GetAIModelName():
                            print("\033[92m" + f"No AI model updates available!" + "\033[0m")
                            return

                    url = "https://huggingface.co/Glas42/NavigationDetectionAI/tree/main/model"
                    response = requests.get(url)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('/Glas42/NavigationDetectionAI/blob/main/model'):
                            LatestAIModel = href.split("/")[-1]
                            settings.Create("NavigationDetectionAI", "LatestModel", LatestAIModel)
                            break

                    CurrentAIModel = GetAIModelName()
                    if CurrentAIModel == "UNKNOWN":
                        CurrentAIModel = None

                    if str(LatestAIModel) != str(CurrentAIModel):
                        LoadAILabel = "Updating AI model..."
                        print("\033[92m" + f"Updating AI model..." + "\033[0m")
                        DeleteAllAIModels()
                        response = requests.get(f"https://huggingface.co/Glas42/NavigationDetectionAI/resolve/main/model/{LatestAIModel}?download=true", stream=True)
                        last_progress = 0
                        with open(os.path.join(f"{variables.PATH}plugins/NavigationDetectionAI/AIModel", f"{LatestAIModel}"), "wb") as modelfile:
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded_size = 0
                            chunk_size = 1024
                            for data in response.iter_content(chunk_size=chunk_size):
                                downloaded_size += len(data)
                                modelfile.write(data)
                                progress = (downloaded_size / total_size) * 100
                                if round(last_progress) < round(progress):
                                    progress_mb = downloaded_size / (1024 * 1024)
                                    total_size_mb = total_size / (1024 * 1024)
                                    LoadAIProgress = progress
                                    LoadAILabel = f"Downloading AI model: {round(progress)}%"
                                    last_progress = progress
                        LoadAIProgress = 100
                        LoadAILabel = "Successfully updated AI model!"
                        print("\033[92m" + f"Successfully updated AI model!" + "\033[0m")
                    else:
                        LoadAIProgress = 100
                        LoadAILabel = "No AI model updates available!"
                        print("\033[92m" + f"No AI model updates available!" + "\033[0m")
                    settings.Create("NavigationDetectionAI", "LastUpdateCheck", time.time())

                else:

                    console.RestoreConsole()
                    print("\033[91m" + f"Connection to https://huggingface.co/ is most likely not available in your country. Unable to check for AI model updates." + "\033[0m")
                    LoadAIProgress = 0
                    LoadAILabel = "Connection to https://huggingface.co/ is\nmost likely not available in your country.\nUnable to check for AI model updates."

            except Exception as ex:
                exc = traceback.format_exc()
                SendCrashReport("NavigationDetection - Error in function CheckForAIModelUpdatesThread.", str(exc))
                print(f"NavigationDetection - Error in function CheckForAIModelUpdatesThread: {ex}")
                console.RestoreConsole()
                print("\033[91m" + f"Failed to check for AI model updates or update the AI model." + "\033[0m")
                LoadAIProgress = 0
                LoadAILabel = "Failed to check for AI model updates or update the AI model."

        global AIModelUpdateThread
        AIModelUpdateThread = threading.Thread(target=CheckForAIModelUpdatesThread)
        AIModelUpdateThread.start()

    except Exception as ex:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function CheckForAIModelUpdates.", str(exc))
        print(f"NavigationDetection - Error in function CheckForAIModelUpdates: {ex}")
        console.RestoreConsole()
        print("\033[91m" + f"Failed to check for AI model updates or update the AI model." + "\033[0m")


def ModelFolderExists():
    try:
        if os.path.exists(f"{variables.PATH}plugins/NavigationDetectionAI/AIModel") == False:
            os.makedirs(f"{variables.PATH}plugins/NavigationDetectionAI/AIModel")
    except Exception as ex:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function ModelFolderExists.", str(exc))
        print(f"NavigationDetection - Error in function ModelFolderExists: {ex}")
        console.RestoreConsole()


def GetAIModelName():
    try:
        ModelFolderExists()
        for file in os.listdir(f"{variables.PATH}plugins/NavigationDetectionAI/AIModel"):
            if file.endswith(".pt"):
                return file
        return "UNKNOWN"
    except Exception as ex:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function GetAIModelName.", str(exc))
        print(f"NavigationDetection - Error in function GetAIModelName: {ex}")
        console.RestoreConsole()
        return "UNKNOWN"


def DeleteAllAIModels():
    try:
        ModelFolderExists()
        for file in os.listdir(f"{variables.PATH}plugins/NavigationDetectionAI/AIModel"):
            if file.endswith(".pt"):
                os.remove(os.path.join(f"{variables.PATH}plugins/NavigationDetectionAI/AIModel", file))
    except PermissionError as ex:
        global TorchAvailable
        TorchAvailable = False
        settings.CreateSettings("NavigationDetection", "UseAI", False)
        print(f"NavigationDetection - PermissionError in function DeleteAllAIModels: {ex}")
        print("NavigationDetectionAI will be automatically disabled because the code cannot delete the AI model.")
        console.RestoreConsole()
    except Exception as ex:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function DeleteAllAIModels.", str(exc))
        print(f"NavigationDetection - Error in function DeleteAllAIModels: {ex}")
        console.RestoreConsole()


def GetAIModelProperties():
    global MODEL_METADATA
    global IMG_WIDTH
    global IMG_HEIGHT
    global IMG_CHANNELS
    global MODEL_OUTPUTS
    global MODEL_EPOCHS
    global MODEL_BATCH_SIZE
    global MODEL_IMAGE_COUNT
    global MODEL_TRAINING_TIME
    global MODEL_TRAINING_DATE
    try:
        ModelFolderExists()
        MODEL_METADATA = {"data": []}
        IMG_WIDTH = "UNKNOWN"
        IMG_HEIGHT = "UNKNOWN"
        IMG_CHANNELS = "UNKNOWN"
        MODEL_OUTPUTS = "UNKNOWN"
        MODEL_EPOCHS = "UNKNOWN"
        MODEL_BATCH_SIZE = "UNKNOWN"
        MODEL_IMAGE_COUNT = "UNKNOWN"
        MODEL_TRAINING_TIME = "UNKNOWN"
        MODEL_TRAINING_DATE = "UNKNOWN"
        if GetAIModelName() == "UNKNOWN" or TorchAvailable == False:
            return
        torch.jit.load(os.path.join(f"{variables.PATH}plugins/NavigationDetectionAI/AIModel", GetAIModelName()), _extra_files=MODEL_METADATA, map_location=AIDevice)
        MODEL_METADATA = str(MODEL_METADATA["data"]).replace('b"(', '').replace(')"', '').replace("'", "").split(", ")
        for var in MODEL_METADATA:
            if "image_width" in var:
                IMG_WIDTH = int(var.split("#")[1])
            if "image_height" in var:
                IMG_HEIGHT = int(var.split("#")[1])
            if "image_channels" in var:
                IMG_CHANNELS = str(var.split("#")[1])
            if "outputs" in var:
                MODEL_OUTPUTS = int(var.split("#")[1])
            if "epochs" in var:
                MODEL_EPOCHS = int(var.split("#")[1])
            if "batch" in var:
                MODEL_BATCH_SIZE = int(var.split("#")[1])
            if "image_count" in var:
                MODEL_IMAGE_COUNT = int(var.split("#")[1])
            if "training_time" in var:
                MODEL_TRAINING_TIME = var.split("#")[1]
            if "training_date" in var:
                MODEL_TRAINING_DATE = var.split("#")[1]
    except Exception as ex:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function GetAIModelProperties.", str(exc))
        print(f"NavigationDetection - Error in function GetAIModelProperties: {ex}")
        console.RestoreConsole()


def plugin():
    start = time.time()

    global enabled
    global enable_key
    global enable_key_pressed
    global last_enable_key_pressed

    global AIDevice
    global LoadAILabel
    global LoadAIProgress

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

    print(f"Offset: {SteeringOffset}, Smoothness: {SteeringSmoothness}, Sensitivity: {SteeringSensitivity}, Maximum: {SteeringMaximum}")

    data = {}
    data["api"] = TruckSimAPI.update()
    data["frame"] = ScreenCapture.plugin(imgtype="cropped")

    current_time = time.time()

    try:
        try:
            while AIModelUpdateThread.is_alive(): return 0
            while AIModelLoadThread.is_alive(): return 0
        except:
            return 0

        try:
            frame = data["frame"]
            width = frame.shape[1]
            height = frame.shape[0]
        except:
            return 0

        if frame is None: return 0
        if width <= 0 or width == None: return 0
        if height <= 0 or height == None: return 0

        if isinstance(frame, np.ndarray) and frame.ndim == 3 and frame.size > 0:
            valid_frame = True
        else:
            valid_frame = False
            return 0

        enable_key_pressed = keyboard.is_pressed(enable_key)
        if enable_key_pressed == False and last_enable_key_pressed == True:
            enabled = not enabled
        last_enable_key_pressed = enable_key_pressed

        cv2.rectangle(frame, (0, 0), (round(frame.shape[1]/6), round(frame.shape[0]/3)), (0, 0, 0), -1)
        cv2.rectangle(frame, (frame.shape[1] ,0), (round(frame.shape[1]-frame.shape[1]/6), round(frame.shape[0]/3)), (0, 0, 0), -1)
        lower_red = np.array([160, 0, 0])
        upper_red = np.array([255, 110, 110])
        mask = cv2.inRange(frame, lower_red, upper_red)
        frame_with_mask = cv2.bitwise_and(frame, frame, mask=mask)
        frame = cv2.cvtColor(frame_with_mask, cv2.COLOR_BGR2GRAY)

        try:
            AIFrame = preprocess_image(mask)
            output = [[0] * MODEL_OUTPUTS]
        except:
            GetAIModelProperties()
            if IMG_WIDTH == "UNKNOWN" or IMG_HEIGHT == "UNKNOWN" or MODEL_OUTPUTS == "UNKNOWN":
                print(f"NavigationDetection - Unable to read the AI model metadata. The code wont run the NavigationDetectionAI.")
                global TorchAvailable
                TorchAvailable = False
                console.RestoreConsole()
                return 0
            AIFrame = preprocess_image(mask)
            output = [[0] * MODEL_OUTPUTS]

        if enabled == True:
            if AIModelLoaded == True:
                with torch.no_grad():
                    output = AIModel(AIFrame)
                    output = output.tolist()

        steering = float(output[0][0]) / -30
        left_indicator = bool(float(output[0][1]) > 0.15)
        right_indicator = bool(float(output[0][2]) > 0.15)

        try:
            indicator_left = data["api"]["truckBool"]["blinkerLeftActive"]
            indicator_right = data["api"]["truckBool"]["blinkerRightActive"]
        except:
            indicator_left = False
            indicator_right = False

        if enabled == True:
            if left_indicator != indicator_left and indicator_left_wait_for_response == False:
                SDKController.lblinker = True
                indicator_left_wait_for_response = True
                indicator_left_response_timer = current_time
            if right_indicator != indicator_right and indicator_right_wait_for_response == False:
                SDKController.rblinker = True
                indicator_right_wait_for_response = True
                indicator_right_response_timer = current_time

            if indicator_left != indicator_last_left:
                indicator_left_wait_for_response = False
            if indicator_right != indicator_last_right:
                indicator_right_wait_for_response = False
            if current_time - 1 > indicator_left_response_timer:
                indicator_left_wait_for_response = False
            if current_time - 1 > indicator_right_response_timer:
                indicator_right_wait_for_response = False
        indicator_last_left = left_indicator
        indicator_last_right = right_indicator

        SDKController.steering = steering

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
                hicon = win32gui.LoadImage(None, f"{variables.PATH}assets/favicon.ico", win32con.IMAGE_ICON, 0, 0, icon_flags)
                win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
                win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

        cv2.imshow("Lane Assist", frame)
        cv2.waitKey(1)

    except Exception as e:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Running AI Error.", str(exc))
        console.RestoreConsole()
        print("\033[91m" + f"NavigationDetection - Running AI Error: " + "\033[0m" + str(e))

    return 1/(time.time() - start)