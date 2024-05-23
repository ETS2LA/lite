from plugins.SDKController.main import SCSController as SCSController
from plugins.TruckSimAPI.main import scsTelemetry as SCSTelemetry
import plugins.ScreenCapture.main as ScreenCapture
from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import src.console as console
import numpy as np
import subprocess
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


def Initialize():
    global enabled
    global enable_key
    global enable_key_pressed
    global last_enable_key_pressed

    global AIDevice
    global LoadAILabel
    global LoadAIProgress

    global map_topleft
    global map_bottomright

    global indicator_last_left
    global indicator_last_right
    global indicator_left_wait_for_response
    global indicator_right_wait_for_response
    global indicator_left_response_timer
    global indicator_right_response_timer

    global SDKController
    global TruckSimAPI

    enabled = True
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

    map_topleft = settings.Get("NavigationDetectionAI", "map_topleft", "unset")
    map_bottomright = settings.Get("NavigationDetectionAI", "map_bottomright", "unset")

    if map_topleft == "unset":
        map_topleft = None
    if map_bottomright == "unset":
        map_bottomright = None

    indicator_last_left = False
    indicator_last_right = False
    indicator_left_wait_for_response = False
    indicator_right_wait_for_response = False
    indicator_left_response_timer = 0
    indicator_right_response_timer = 0

    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()

    while TruckSimAPI.update()["scsValues"]["telemetryPluginRevision"] < 2:
        time.sleep(0.1)

    ScreenCapture.Initialize(settings.Get("ScreenCapture", "display", 0))

    cv2.namedWindow('Lane Assist', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Lane Assist', cv2.WND_PROP_TOPMOST, 1)

    if variables.OS == "nt":
        hwnd = win32gui.FindWindow(None, "Lane Assist")
        windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, byref(c_int(0x000000)), sizeof(c_int))
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        hicon = win32gui.LoadImage(None, f"{variables.PATH}assets/favicon.ico", win32con.IMAGE_ICON, 0, 0, icon_flags)
        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)


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
                global IMG_WIDTH
                global IMG_HEIGHT

                CheckForAIModelUpdates()
                while AIModelUpdateThread.is_alive(): time.sleep(0.1)

                if GetAIModelName() == []:
                    return

                LoadAIProgress = 0
                LoadAILabel = "Loading the AI model..."

                print("\033[92m" + f"Loading the AI model..." + "\033[0m")

                IMG_WIDTH = GetAIModelProperties()[2]
                IMG_HEIGHT = GetAIModelProperties()[3]

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

                    url = "https://huggingface.co/Glas42/NavigationDetectionAI/tree/main/model"
                    response = requests.get(url)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('/Glas42/NavigationDetectionAI/blob/main/model'):
                            LatestAIModel = href.split("/")[-1]
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
    except Exception as ex:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function DeleteAllAIModels.", str(exc))
        print(f"NavigationDetection - Error in function DeleteAllAIModels: {ex}")
        console.RestoreConsole()


def GetAIModelProperties():
    try:
        ModelFolderExists()
        if GetAIModelName() == "UNKNOWN":
            return ("UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN")
        else:
            string = str(GetAIModelName())
            if string != "UNKNOWN":
                epochs = int(string.split("EPOCHS-")[1].split("_")[0])
                batch = int(string.split("BATCH-")[1].split("_")[0])
                img_width = int(string.split("IMG_WIDTH-")[1].split("_")[0])
                img_height = int(string.split("IMG_HEIGHT-")[1].split("_")[0])
                img_count = int(string.split("IMG_COUNT-")[1].split("_")[0])
                training_time = string.split("TIME-")[1].split("_")[0]
                training_date = string.split("DATE-")[1].split(".")[0]
                return (epochs, batch, img_width, img_height, img_count, training_time, training_date)
            else:
                return ("UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN")
    except Exception as ex:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function GetAIModelProperties.", str(exc))
        print(f"NavigationDetection - Error in function GetAIModelProperties: {ex}")
        console.RestoreConsole()
        return ("UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN")


def plugin():
    global enabled
    global enable_key
    global enable_key_pressed
    global last_enable_key_pressed

    global AIDevice
    global LoadAILabel
    global LoadAIProgress

    global map_topleft
    global map_bottomright

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
    if data["api"]["scsValues"]["telemetryPluginRevision"] < 2:
        print("TruckSimAPI is waiting for the game...")
        time.sleep(0.1)
        while TruckSimAPI.update()["scsValues"]["telemetryPluginRevision"] < 2:
            time.sleep(0.1)
    data["frame"] = ScreenCapture.plugin(imgtype="cropped")

    current_time = time.time()

    try:
        global IMG_WIDTH
        global IMG_HEIGHT

        try:
            while AIModelUpdateThread.is_alive(): return
            while AIModelLoadThread.is_alive(): return
        except:
            return

        try:
            frame = data["frame"]
            width = frame.shape[1]
            height = frame.shape[0]
        except:
            return

        if frame is None: return
        if width == 0 or width == None: return
        if height == 0 or height == None: return
        
        if isinstance(frame, np.ndarray) and frame.ndim == 3 and frame.size > 0:
            valid_frame = True
        else:
            valid_frame = False
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

        try:
            AIFrame = preprocess_image(mask)
        except:
            IMG_WIDTH = GetAIModelProperties()[2]
            IMG_HEIGHT = GetAIModelProperties()[3]
            if IMG_WIDTH == "UNKNOWN" or IMG_HEIGHT == "UNKNOWN":
                print(f"NavigationDetection - Unable to read the AI model image size. Make sure you didn't change the model file name. The code wont run the NavigationDetectionAI.")
                console.RestoreConsole()
                return
            AIFrame = preprocess_image(mask)

        output = [[0, 0, 0, 0, 0, 0, 0, 0]]

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

        if left_indicator != indicator_left:
            SCSController.lblinker = True
            indicator_left_wait_for_response = True
            indicator_left_response_timer = current_time
        if right_indicator != indicator_right:
            SCSController.rblinker = True
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

        SCSController.steering = steering

        cv2.imshow("Lane Assist", frame)
        cv2.waitKey(1)

    except Exception as e:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Running AI Error.", str(exc))
        console.RestoreConsole()
        print("\033[91m" + f"NavigationDetection - Running AI Error: " + "\033[0m" + str(e))


class UI():
    try:
        def __init__(self, master) -> None:
            self.master = master
            self.exampleFunction()
            resizeWindow(950,600)        

        def destroy(self):
            self.done = True
            self.root.destroy()
            del self

        def tabFocused(self):
            resizeWindow(950,600)

        def UpdateSettings(self):

            self.UI_offset.set(self.UI_offsetSlider.get())
            self.UI_lanechanging_speed.set(self.UI_lanechanging_speedSlider.get())
            self.UI_lanechanging_width.set(self.UI_lanechanging_widthSlider.get())

            settings.CreateSettings("NavigationDetectionAI", "offset", self.UI_offsetSlider.get())
            settings.CreateSettings("NavigationDetectionAI", "lanechanging_speed", self.UI_lanechanging_speedSlider.get())
            settings.CreateSettings("NavigationDetectionAI", "lanechanging_width", self.UI_lanechanging_widthSlider.get())

            LoadSettings()

        def exampleFunction(self):

            try:
                self.root.destroy()
            except: pass

            self.root = tk.Canvas(self.master, width=950, height=600, border=0, highlightthickness=0)
            self.root.grid_propagate(1)
            self.root.pack_propagate(0)

            notebook = ttk.Notebook(self.root)
            notebook.pack(anchor="center", fill="both", expand=True)

            generalFrame = ttk.Frame(notebook)
            generalFrame.pack()
            setupFrame = ttk.Frame(notebook)
            setupFrame.pack()
            advancedFrame = ttk.Frame(notebook)
            advancedFrame.pack()
            navigationdetectionaiFrame = ttk.Frame(notebook)
            navigationdetectionaiFrame.pack()

            notebook.add(generalFrame, text=Translate("General"))
            notebook.add(setupFrame, text=Translate("Setup"))
            notebook.add(advancedFrame, text=Translate("Advanced"))
            notebook.add(navigationdetectionaiFrame, text=Translate("NavigationDetectionAI"))

            self.root.pack(anchor="center", expand=False)
            self.root.update()

            ############################################################################################################################
            # UI
            ############################################################################################################################

            self.UI_offsetSlider = tk.Scale(generalFrame, from_=-20, to=20, resolution=0.1, orient=tk.HORIZONTAL, length=500, command=lambda x: self.UpdateSettings())
            self.UI_offsetSlider.set(settings.GetSettings("NavigationDetection", "offset"))
            self.UI_offsetSlider.grid(row=2, column=0, padx=10, pady=0, columnspan=2)
            self.UI_offset = helpers.MakeComboEntry(generalFrame, "Lane Offset", "NavigationDetection", "offset", 2, 0, labelwidth=10, width=8, isFloat=True, sticky="ne")

            helpers.MakeEmptyLine(generalFrame, 3, 0)

            helpers.MakeCheckButton(generalFrame, "Left-hand traffic\n----------------------\nEnable this if you are driving in a country with left-hand traffic.", "NavigationDetection", "lefthand_traffic", 4, 0, width=80, callback=lambda: LoadSettings())

            helpers.MakeEmptyLine(generalFrame, 5, 0)

            helpers.MakeCheckButton(generalFrame, "Lane Changing\n---------------------\nIf enabled, you can change the lane you are driving on using the games indicators\nor the buttons you set in the Controls menu.", "NavigationDetection", "lanechanging_do_lane_changing", 6, 0, width=80, callback=lambda: LoadSettings())

            self.UI_lanechanging_speedSlider = tk.Scale(generalFrame, from_=0.1, to=3, resolution=0.1, orient=tk.HORIZONTAL, length=500, command=lambda x: self.UpdateSettings())
            self.UI_lanechanging_speedSlider.set(settings.GetSettings("NavigationDetection", "lanechanging_speed"))
            self.UI_lanechanging_speedSlider.grid(row=7, column=0, padx=10, pady=0, columnspan=2)
            self.UI_lanechanging_speed = helpers.MakeComboEntry(generalFrame, "Lane Changing Speed", "NavigationDetection", "lanechanging_speed", 7, 0, labelwidth=18, width=8, isFloat=True, sticky="ne")

            helpers.MakeLabel(generalFrame, "╚> This slider sets the speed of the lane changing.", 8, 0, sticky="nw")

            self.UI_lanechanging_widthSlider = tk.Scale(generalFrame, from_=1, to=30, resolution=0.1, orient=tk.HORIZONTAL, length=500, command=lambda x: self.UpdateSettings())
            self.UI_lanechanging_widthSlider.set(settings.GetSettings("NavigationDetection", "lanechanging_width"))
            self.UI_lanechanging_widthSlider.grid(row=9, column=0, padx=10, pady=0, columnspan=2)
            self.UI_lanechanging_width = helpers.MakeComboEntry(generalFrame, "Lane Width", "NavigationDetection", "lanechanging_width", 9, 0, labelwidth=18, width=8, isFloat=True, sticky="ne")

            helpers.MakeLabel(generalFrame, "╚> This slider sets how much the truck needs to go left or right to change the lane.", 10, 0, sticky="nw")

            helpers.MakeEmptyLine(generalFrame, 11, 0)

            helpers.MakeButton(generalFrame, "Give feedback, report a bug or suggest a new feature", lambda: switchSelectedPlugin("plugins.Feedback.main"), 12, 0, width=80, sticky="nw")

            helpers.MakeButton(generalFrame, "Open Wiki", lambda: OpenWiki(), 12, 1, width=23, sticky="nw")

            def OpenWiki():
                browser = helpers.Dialog("Wiki","In which brower should the wiki be opened?", ["In-app browser", "External browser"], "In-app browser", "External Browser")
                if browser == "In-app browser":
                    from src.mainUI import closeTabName
                    from plugins.Wiki.main import LoadURL
                    closeTabName("Wiki")
                    LoadURL("https://wiki.tumppi066.fi/plugins/navigationdetection")
                else:
                    helpers.OpenInBrowser("https://wiki.tumppi066.fi/plugins/navigationdetection")


            helpers.MakeLabel(setupFrame, "Choose a setup method:", 1, 0, font=("Robot", 12, "bold"), sticky="nw")

            helpers.MakeButton(setupFrame, "Automatic Setup", self.automatic_setup, 2, 0, sticky="nw")

            helpers.MakeLabel(setupFrame, "The automatic setup will search for the minimap on your screen using AI (YOLOv5), it needs to download some\nfiles the first time you run it. Make sure that the minimap is always visible and not blocked by other applications.", 3, 0, sticky="nw")

            helpers.MakeEmptyLine(setupFrame, 4, 0)

            helpers.MakeButton(setupFrame, "Manual Setup", self.manual_setup, 5, 0, sticky="nw")

            helpers.MakeLabel(setupFrame, "The manual setup will take a screenshot of your screen and then ask you to select the minimap and arrow positions.\nYou can take a look at the example image when you don't know what to do. The example image will open in another window.", 6, 0, sticky="nw")


            helpers.MakeCheckButton(advancedFrame, "Automatically change to lane 0 if a turn got detected and lane changing is enabled.\nNote: If disabled, you will be unable to change lanes when detecting a turn.", "NavigationDetection", "lanechanging_autolanezero", 2, 0, width=97, callback=lambda: LoadSettings())

            helpers.MakeLabel(navigationdetectionaiFrame, "NavigationDetectionAI", 1, 0, font=("Robot", 14, "bold"), sticky="nw")

            helpers.MakeLabel(navigationdetectionaiFrame, "A PyTorch AI which drives the truck using images of the route advisor.", 2, 0, sticky="nw")

            helpers.MakeCheckButton(navigationdetectionaiFrame, "Use NavigationDetectionAI instead of NavigationDetection.", "NavigationDetection", "UseAI", 3, 0, width=97, callback=lambda: {LoadSettings(), self.exampleFunction()})

            if UseAI:

                helpers.MakeCheckButton(navigationdetectionaiFrame, f"Try to use your GPU with CUDA instead of your CPU to run the AI.\n(Currently using {str(AIDevice).upper()})", "NavigationDetection", "UseCUDA", 4, 0, width=97, callback=lambda: {LoadSettings(), self.exampleFunction()})

                def InstallCUDAPopup():
                    helpers.Dialog("Warning: CUDA is only available for NVIDIA GPUs!", f"1. Check on https://wikipedia.org/wiki/CUDA#GPUs_supported which CUDA version your GPU supports.\n2. Go to https://pytorch.org/ and copy the download command for the corresponding CUDA version which is compatible with your GPU.\n    (Select Stable, Windows, Pip, Python and the CUDA version you need)\n3. Open your file explorer and go to {os.path.dirname(os.path.dirname(variables.PATH))} and run the activate.bat\n4. Run this command in the terminal which opened after running the activate.bat: 'pip uninstall torch torchvision torchaudio'\n5. After the previous command finished, run the command you copied from the PyTorch website and wait for the installation to finish.\n6. Restart the app and the app should automatically detect CUDA as available and use your GPU for the AI.", ["Exit"], "Exit")

                helpers.MakeButton(navigationdetectionaiFrame, "Install CUDA for GPU support", InstallCUDAPopup, 5, 0, width=30, sticky="nw")

                model_properties = GetAIModelProperties()

                helpers.MakeLabel(navigationdetectionaiFrame, "Model properties:", 6, 0, font=("Robot", 12, "bold"), sticky="nw")
            
                helpers.MakeLabel(navigationdetectionaiFrame, f"Epochs: {model_properties[0]}\nBatch Size: {model_properties[1]}\nImage Width: {model_properties[2]}\nImage Height: {model_properties[3]}\nImages/Data Points: {model_properties[4]}\nTraining Time: {model_properties[5]}\nTraining Date: {model_properties[6]}", 7, 0, sticky="nw")

                self.progresslabel = helpers.MakeLabel(navigationdetectionaiFrame, "", 9, 0, sticky="nw")

                self.progress = ttk.Progressbar(navigationdetectionaiFrame, orient="horizontal", length=238, mode="determinate")
                self.progress.grid(row=10, column=0, sticky="nw", padx=5, pady=0)

                def UIButtonCheckForModelUpdates():
                    CheckForAIModelUpdates()
                    while AIModelUpdateThread.is_alive(): time.sleep(0.1)
                    if TorchAvailable == True:
                        LoadAIModel()
                    else:
                        print("NavigationDetectionAI not available due to missing dependencies.")
                        console.RestoreConsole()

                helpers.MakeButton(navigationdetectionaiFrame, "Check for AI model updates", UIButtonCheckForModelUpdates, 11, 0, width=30, sticky="nw")

        def save(self):
            LoadSettings()

        def manual_setup(self):
            found_venv = True
            if os.path.exists(f"{os.path.dirname(os.path.dirname(variables.PATH))}/venv/Scripts/python.exe") == False:
                print("\033[91m" + "Your installation is missing the venv. This is probably because you didn't install the app using the installer." + "\033[0m")
                found_venv = False
            if os.path.exists(f"{variables.PATH}plugins/NavigationDetectionAI/manual_setup.py") == True:
                if found_venv == True:
                    subprocess.Popen([f"{os.path.dirname(os.path.dirname(variables.PATH))}/venv/Scripts/python.exe", os.path.join(variables.PATH, "plugins/NavigationDetection", "manual_setup.py")], shell=True)
                else:
                    print("\033[91m" + "Running the code outside of the venv. You may need to install the requirements manually using this command in a terminal: " + "\033[0m" + "pip install tk numpy mouse opencv-python mss" + "\033[0m")
                    subprocess.Popen(["python", os.path.join(variables.PATH, "plugins", "NavigationDetection", "manual_setup.py")])
            else:
                print("\033[91m" + f"Your installation is missing the manual_setup.py. Download it manually from the GitHub and place it in this path: {variables.PATH}plugins\\NavigationDetection\\manual_setup.py" + "\033[0m")

        def automatic_setup(self):
            found_venv = True
            if os.path.exists(f"{os.path.dirname(os.path.dirname(variables.PATH))}/venv/Scripts/python.exe") == False:
                print("\033[91m" + "Your installation is missing the venv. This is probably because you didn't install the app using the installer." + "\033[0m")
                found_venv = False
            if os.path.exists(f"{variables.PATH}plugins/NavigationDetectionAI/automatic_setup.py") == True:
                if found_venv == True:
                    subprocess.Popen([f"{os.path.dirname(os.path.dirname(variables.PATH))}/venv/Scripts/python.exe", os.path.join(variables.PATH, "plugins/NavigationDetection", "automatic_setup.py")], shell=True)
                else:
                    print("\033[91m" + "Running the code outside of the venv. You may need to install the requirements manually using this command in a terminal: " + "\033[0m" + "pip install tk numpy requests mouse opencv-python mss torch" + "\033[0m")
                    subprocess.Popen(["python", os.path.join(variables.PATH, "plugins", "NavigationDetection", "automatic_setup.py")])
            else:
                print("\033[91m" + f"Your installation is missing the automatic_setup.py. Download it manually from the GitHub and place it in this path: {variables.PATH}plugins\\NavigationDetection\\automatic_setup.py" + "\033[0m")

        def update(self, data):
            if UseAI:
                self.progresslabel.set(LoadAILabel)
                self.progress["value"] = LoadAIProgress
            self.root.update()

    except Exception as ex:
        print(ex.args)

# this comment is used to reload the app after finishing the setup - 0