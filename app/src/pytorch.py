from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import src.console as console
from bs4 import BeautifulSoup
import threading
import traceback
import requests
import torch
import time
import os

RED = "\033[91m"
GREEN = "\033[92m"
DARK_GREY = "\033[90m"
NORMAL = "\033[0m"

try:
    from torchvision import transforms
    import torch
    TorchAvailable = True
except:
    TorchAvailable = False
    exc = traceback.format_exc()
    SendCrashReport("NavigationDetectionAI - PyTorch import error.", str(exc))
    print(RED + "NavigationDetectionAI - PyTorch import error:\n" + NORMAL + str(exc))
    console.RestoreConsole()


AIModelUpdateThread = None
AIModelLoadThread = None


def Initialize():
    global DEVICE
    global PATH

    TryCuda = settings.Get("PyTorch", "TryCuda", True)
    DEVICE = torch.device("cuda" if torch.cuda.is_available() and TryCuda else "cpu")
    PATH = f"{variables.PATH}cache/NavigationDetectionAI"


def LoadAIModel():
    try:
        def LoadAIModelThread():
            try:
                global Model
                global ModelLoaded

                CheckForAIModelUpdates()
                while AIModelUpdateThread.is_alive():
                    time.sleep(0.1)

                if GetAIModelName() == None:
                    return

                variables.QUEUE.put(["Loading the AI model...", 0, 0.5])
                print(GREEN + "Loading the AI model..." + NORMAL)

                GetAIModelProperties()

                ModelFileCorrupted = False

                try:
                    Model = torch.jit.load(os.path.join(PATH, GetAIModelName()), map_location=DEVICE)
                    Model.eval()
                except:
                    ModelFileCorrupted = True

                if ModelFileCorrupted == False:
                    variables.QUEUE.put(["Successfully loaded the AI model!", 100, 0.5])
                    print(GREEN + "Successfully loaded the AI model!" + NORMAL)
                    ModelLoaded = True
                else:
                    variables.QUEUE.put(["Failed to load the AI model because the model file is corrupted.", 0, 0.5])
                    print(RED + "Failed to load the AI model because the model file is corrupted." + NORMAL)
                    ModelLoaded = False
                    time.sleep(3)
                    HandleCorruptedAIModel()
            except:
                exc = traceback.format_exc()
                SendCrashReport("NavigationDetection - Loading AI Error.", str(exc))
                print(RED + "NavigationDetection - Loading AI Error:\n" + NORMAL + str(exc))
                console.RestoreConsole()
                variables.QUEUE.put(["Failed to load the AI model!", 0, 0.5])
                print(RED + "Failed to load the AI model!" + NORMAL)
                ModelLoaded = False

        if TorchAvailable:
            global AIModelLoadThread
            AIModelLoadThread = threading.Thread(target=LoadAIModelThread, daemon=True)
            AIModelLoadThread.start()

    except:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function LoadAIModel.", str(exc))
        print(RED + "NavigationDetection - Error in function LoadAIModel:\n" + NORMAL + str(exc))
        console.RestoreConsole()


def CheckForAIModelUpdates():
    try:
        def CheckForAIModelUpdatesThread():
            try:
                try:
                    response = requests.get("https://huggingface.co/", timeout=3)
                    response = response.status_code
                except requests.exceptions.RequestException:
                    response = None

                if response == 200:
                    variables.QUEUE.put(["Checking for AI model updates...", 0, 0.5])
                    print(GREEN + "Checking for AI model updates..." + NORMAL)

                    if settings.Get("NavigationDetectionAI", "LastUpdateCheck", 0) + 600 > time.time():
                        if settings.Get("NavigationDetectionAI", "LatestModel", "unset") == GetAIModelName():
                            print(GREEN + "No AI model updates available!" + NORMAL)
                            return

                    url = "https://huggingface.co/Glas42/NavigationDetectionAI/tree/main/model"
                    response = requests.get(url)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('/Glas42/NavigationDetectionAI/blob/main/model'):
                            LatestAIModel = href.split("/")[-1]
                            settings.Set("NavigationDetectionAI", "LatestModel", LatestAIModel)
                            break

                    CurrentAIModel = GetAIModelName()

                    if str(LatestAIModel) != str(CurrentAIModel):
                        variables.QUEUE.put(["Updating the AI model...", 0, 0.5])
                        print(GREEN + "Updating the AI model..." + NORMAL)
                        DeleteAllAIModels()
                        response = requests.get(f"https://huggingface.co/Glas42/NavigationDetectionAI/resolve/main/model/{LatestAIModel}?download=true", stream=True)
                        with open(os.path.join(PATH, f"{LatestAIModel}"), "wb") as modelfile:
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded_size = 0
                            chunk_size = 1024
                            for data in response.iter_content(chunk_size=chunk_size):
                                downloaded_size += len(data)
                                modelfile.write(data)
                                progress = round((downloaded_size / total_size) * 100)
                                variables.QUEUE.put([f"Downloading the AI model: {progress}%", progress, 0.5])
                        variables.QUEUE.put(["Successfully updated the AI model!", 100, 0.5])
                        print(GREEN + "Successfully updated the AI model!" + NORMAL)
                    else:
                        variables.QUEUE.put(["No AI model updates available!", 100, 0.5])
                        print(GREEN + "No AI model updates available!" + NORMAL)
                    settings.Set("NavigationDetectionAI", "LastUpdateCheck", time.time())

                else:

                    console.RestoreConsole()
                    variables.QUEUE.put(["Connection to https://huggingface.co/ is most likely not available in your country. Unable to check for AI model updates.", 0, 0.5])
                    print(RED + "Connection to https://huggingface.co/ is most likely not available in your country. Unable to check for AI model updates." + NORMAL)

            except:
                exc = traceback.format_exc()
                SendCrashReport("NavigationDetection - Error in function CheckForAIModelUpdatesThread.", str(exc))
                print(RED + "NavigationDetection - Error in function CheckForAIModelUpdatesThread:\n" + NORMAL + str(exc))
                console.RestoreConsole()
                variables.QUEUE.put(["Failed to check for AI model updates or update the AI model.", 0, 0.5])
                print(RED + "Failed to check for AI model updates or update the AI model." + NORMAL)

        global AIModelUpdateThread
        AIModelUpdateThread = threading.Thread(target=CheckForAIModelUpdatesThread, daemon=True)
        AIModelUpdateThread.start()

    except:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function CheckForAIModelUpdates.", str(exc))
        print(RED + "NavigationDetection - Error in function CheckForAIModelUpdates:\n" + NORMAL + str(exc))
        console.RestoreConsole()
        variables.QUEUE.put(["Failed to check for AI model updates or update the AI model.", 0, 0.5])
        print(RED + "Failed to check for AI model updates or update the AI model." + NORMAL)


def ModelFolderExists():
    try:
        if os.path.exists(PATH) == False:
            os.makedirs(PATH)
    except:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function ModelFolderExists.", str(exc))
        print(RED + "NavigationDetection - Error in function ModelFolderExists:\n" + NORMAL + str(exc))
        console.RestoreConsole()


def GetAIModelName():
    try:
        ModelFolderExists()
        for file in os.listdir(PATH):
            if file.endswith(".pt"):
                return file
        return None
    except:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetection - Error in function GetAIModelName.", str(exc))
        print(RED + "NavigationDetectionAI - Error in function GetAIModelName:\n" + NORMAL + str(exc))
        console.RestoreConsole()
        return None


def DeleteAllAIModels():
    try:
        ModelFolderExists()
        for file in os.listdir(PATH):
            if file.endswith(".pt"):
                os.remove(os.path.join(PATH, file))
    except PermissionError:
        global TorchAvailable
        TorchAvailable = False
        exc = traceback.format_exc()
        print(RED + "NavigationDetectionAI - PermissionError in function DeleteAllAIModels:\n" + NORMAL + str(exc))
        console.RestoreConsole()
    except:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetectionAI - Error in function DeleteAllAIModels.", str(exc))
        print(RED + "NavigationDetectionAI - Error in function DeleteAllAIModels:\n" + NORMAL + str(exc))
        console.RestoreConsole()


def HandleCorruptedAIModel():
    DeleteAllAIModels()
    CheckForAIModelUpdates()
    while AIModelUpdateThread.is_alive():
        time.sleep(0.1)
    time.sleep(0.5)
    if TorchAvailable == True:
        LoadAIModel()


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
        IMG_WIDTH = None
        IMG_HEIGHT = None
        IMG_CHANNELS = None
        MODEL_OUTPUTS = None
        MODEL_EPOCHS = None
        MODEL_BATCH_SIZE = None
        MODEL_IMAGE_COUNT = None
        MODEL_TRAINING_TIME = None
        MODEL_TRAINING_DATE = None
        if GetAIModelName() == None or TorchAvailable == False:
            return
        torch.jit.load(os.path.join(PATH, GetAIModelName()), _extra_files=MODEL_METADATA, map_location=DEVICE)
        MODEL_METADATA = eval(MODEL_METADATA["data"])
        for item in MODEL_METADATA:
            item = str(item)
            if "image_width" in item:
                IMG_WIDTH = int(item.split("#")[1])
            if "image_height" in item:
                IMG_HEIGHT = int(item.split("#")[1])
            if "image_channels" in item:
                IMG_CHANNELS = str(item.split("#")[1])
            if "outputs" in item:
                MODEL_OUTPUTS = int(item.split("#")[1])
            if "epochs" in item:
                MODEL_EPOCHS = int(item.split("#")[1])
            if "batch" in item:
                MODEL_BATCH_SIZE = int(item.split("#")[1])
            if "image_count" in item:
                MODEL_IMAGE_COUNT = int(item.split("#")[1])
            if "training_time" in item:
                MODEL_TRAINING_TIME = item.split("#")[1]
            if "training_date" in item:
                MODEL_TRAINING_DATE = item.split("#")[1]
    except:
        exc = traceback.format_exc()
        SendCrashReport("NavigationDetectionAI - Error in function GetAIModelProperties.", str(exc))
        print(RED + "NavigationDetectionAI - Error in function GetAIModelProperties:\n" + NORMAL + str(exc))
        console.RestoreConsole()