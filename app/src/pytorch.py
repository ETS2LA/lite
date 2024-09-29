from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import src.console as console
import src.plugins as plugins
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
    SendCrashReport("PyTorch - PyTorch import error.", str(exc))

MODELS = {}

def Initialize(Owner="", Model="", Threaded=True):
    MODELS[Model] = {}
    MODELS[Model]["Device"] = torch.device("cuda" if torch.cuda.is_available() and settings.Get("PyTorch", "TryCuda", True) else "cpu")
    MODELS[Model]["Path"] = f"{variables.PATH}cache/{Model}"
    MODELS[Model]["Threaded"] = Threaded
    MODELS[Model]["ModelOwner"] = str(Owner)


def Load(Model):
    try:
        def LoadFunction(Model):
            try:
                CheckForUpdates(Model)
                if "UpdateThread" in MODELS[Model]:
                    while MODELS[Model]["UpdateThread"].is_alive():
                        time.sleep(0.1)

                if GetName(Model) == None:
                    return

                plugins.AddToQueue({"POPUP": ["Loading the model...", 0, 0.5]})
                print(DARK_GREY + f"[{Model}] " + GREEN + "Loading the model..." + NORMAL)

                GetProperties(Model)

                ModelFileBroken = False

                try:
                    MODELS[Model]["Model"] = torch.jit.load(os.path.join(MODELS[Model]["Path"], GetName(Model)), map_location=MODELS[Model]["Device"])
                    MODELS[Model]["Model"].eval()
                except:
                    ModelFileBroken = True

                if ModelFileBroken == False:
                    plugins.AddToQueue({"POPUP": ["Successfully loaded the model!", 0, 0.5]})
                    print(DARK_GREY + f"[{Model}] " + GREEN + "Successfully loaded the model!" + NORMAL)
                    MODELS[Model]["ModelLoaded"] = True
                else:
                    plugins.AddToQueue({"POPUP": ["Failed to load the model because the model file is broken.", 0, 0.5]})
                    print(DARK_GREY + f"[{Model}] " + RED + "Failed to load the model because the model file is broken." + NORMAL)
                    MODELS[Model]["ModelLoaded"] = False
                    HandleBroken(Model)
            except:
                SendCrashReport("PyTorch - Loading Error.", str(traceback.format_exc()))
                plugins.AddToQueue({"POPUP": ["Failed to load the model!", 0, 0.5]})
                print(DARK_GREY + f"[{Model}] " + RED + "Failed to load the model!" + NORMAL)
                MODELS[Model]["ModelLoaded"] = False

        if TorchAvailable:
            if MODELS[Model]["Threaded"]:
                MODELS[Model]["LoadThread"] = threading.Thread(target=LoadFunction, args=(Model,), daemon=True)
                MODELS[Model]["LoadThread"].start()
            else:
                LoadFunction(Model)

    except:
        SendCrashReport("PyTorch - Error in function Load.", str(traceback.format_exc()))
        plugins.AddToQueue({"POPUP": ["Failed to load the model.", 0, 0.5]})
        print(DARK_GREY + f"[{Model}] " + RED + "Failed to load the model." + NORMAL)


def CheckForUpdates(Model):
    try:
        def CheckForUpdatesFunction(Model):
            try:
                try:
                    response = requests.get("https://huggingface.co/", timeout=3)
                    response = response.status_code
                except requests.exceptions.RequestException:
                    response = None

                if response == 200:
                    plugins.AddToQueue({"POPUP": ["Checking for model updates...", 0, 0.5]})
                    print(DARK_GREY + f"[{Model}] " + GREEN + "Checking for model updates..." + NORMAL)

                    if settings.Get("PyTorch", f"{Model}-LastUpdateCheck", 0) + 600 > time.time():
                        if settings.Get("PyTorch", f"{Model}-LatestModel", "unset") == GetName(Model):
                            print(DARK_GREY + f"[{Model}] " + GREEN + "No model updates available!" + NORMAL)
                            return

                    url = f'https://huggingface.co/{MODELS[Model]["ModelOwner"]}/{Model}/tree/main/model'
                    response = requests.get(url)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    LatestModel = None
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        if href.startswith(f'/{MODELS[Model]["ModelOwner"]}/{Model}/blob/main/model'):
                            LatestModel = href.split("/")[-1]
                            settings.Set("PyTorch", f"{Model}-LatestModel", LatestModel)
                            break
                    if LatestModel == None:
                        LatestModel = settings.Get("PyTorch", f"{Model}-LatestModel", "unset")

                    CurrentModel = GetName(Model)

                    if str(LatestModel) != str(CurrentModel):
                        plugins.AddToQueue({"POPUP": ["Updating the model...", 0, 0.5]})
                        print(DARK_GREY + f"[{Model}] " + GREEN + "Updating the model..." + NORMAL)
                        Delete(Model)
                        response = requests.get(f'https://huggingface.co/{MODELS[Model]["ModelOwner"]}/{Model}/resolve/main/model/{LatestModel}?download=true', stream=True)
                        with open(os.path.join(MODELS[Model]["Path"], f"{LatestModel}"), "wb") as modelfile:
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded_size = 0
                            chunk_size = 1024
                            for data in response.iter_content(chunk_size=chunk_size):
                                downloaded_size += len(data)
                                modelfile.write(data)
                                progress = round((downloaded_size / total_size) * 100)
                                plugins.AddToQueue({"POPUP": [f"Downloading the model: {progress}%", progress, 0.5]})
                        plugins.AddToQueue({"POPUP": ["Successfully updated the model!", 0, 0.5]})
                        print(DARK_GREY + f"[{Model}] " + GREEN + "Successfully updated the model!" + NORMAL)
                    else:
                        plugins.AddToQueue({"POPUP": ["No model updates available!", 0, 0.5]})
                        print(DARK_GREY + f"[{Model}] " + GREEN + "No model updates available!" + NORMAL)
                    settings.Set("PyTorch", f"{Model}-LastUpdateCheck", time.time())

                else:

                    console.RestoreConsole()
                    plugins.AddToQueue({"POPUP": ["Connection to https://huggingface.co/ is most likely not available in your country. Unable to check for model updates.", 0, 0.5]})
                    print(DARK_GREY + f"[{Model}] " + RED + "Connection to https://huggingface.co/ is most likely not available in your country. Unable to check for model updates." + NORMAL)

            except:
                SendCrashReport("PyTorch - Error in function CheckForUpdatesFunction.", str(traceback.format_exc()))
                plugins.AddToQueue({"POPUP": ["Failed to check for model updates or update the model.", 0, 0.5]})
                print(DARK_GREY + f"[{Model}] " + RED + "Failed to check for model updates or update the model." + NORMAL)

        if MODELS[Model]["Threaded"]:
            MODELS[Model]["UpdateThread"] = threading.Thread(target=CheckForUpdatesFunction, args=(Model,), daemon=True)
            MODELS[Model]["UpdateThread"].start()
        else:
            CheckForUpdatesFunction(Model)

    except:
        SendCrashReport("PyTorch - Error in function CheckForUpdates.", str(traceback.format_exc()))
        plugins.AddToQueue({"POPUP": ["Failed to check for model updates or update the model.", 0, 0.5]})
        print(DARK_GREY + f"[{Model}] " + RED + "Failed to check for model updates or update the model." + NORMAL)


def FolderExists(Model):
    try:
        if os.path.exists(MODELS[Model]["Path"]) == False:
            os.makedirs(MODELS[Model]["Path"])
    except:
        SendCrashReport("PyTorch - Error in function FolderExists.", str(traceback.format_exc()))


def GetName(Model):
    try:
        FolderExists(Model)
        for file in os.listdir(MODELS[Model]["Path"]):
            if file.endswith(".pt"):
                return file
        return None
    except:
        SendCrashReport("PyTorch - Error in function GetName.", str(traceback.format_exc()))
        return None


def Delete(Model):
    try:
        FolderExists(Model)
        for file in os.listdir(MODELS[Model]["Path"]):
            if file.endswith(".pt"):
                os.remove(os.path.join(MODELS[Model]["Path"], file))
    except PermissionError:
        global TorchAvailable
        TorchAvailable = False
        print(DARK_GREY + f"[{Model}] " + RED + "PyTorch - PermissionError in function Delete:\n" + NORMAL + str(traceback.format_exc()))
        console.RestoreConsole()
    except:
        SendCrashReport("PyTorch - Error in function Delete.", str(traceback.format_exc()))


def HandleBroken(Model):
    try:
        Delete(Model)
        CheckForUpdates(Model)
        if "UpdateThread" in MODELS[Model]:
            while MODELS[Model]["UpdateThread"].is_alive():
                time.sleep(0.1)
        time.sleep(0.5)
        if TorchAvailable == True:
            Load(Model)
    except:
        SendCrashReport("PyTorch - Error in function HandleBroken.", str(traceback.format_exc()))


def GetProperties(Model):
    try:
        FolderExists(Model)
        MODELS[Model]["Metadata"] = {"data": []}
        if GetName(Model) == None or TorchAvailable == False:
            return
        torch.jit.load(os.path.join(MODELS[Model]["Path"], GetName(Model)), _extra_files=MODELS[Model]["Metadata"], map_location=MODELS[Model]["Device"])
        MODELS[Model]["Metadata"] = eval(MODELS[Model]["Metadata"]["data"])
        for item in MODELS[Model]["Metadata"]:
            item = str(item)
            if "image_width" in item:
                MODELS[Model]["IMG_WIDTH"] = int(item.split("#")[1])
            if "image_height" in item:
                MODELS[Model]["IMG_HEIGHT"] = int(item.split("#")[1])
            if "image_channels" in item:
                MODELS[Model]["IMG_CHANNELS"] = str(item.split("#")[1])
            if "outputs" in item:
                MODELS[Model]["OUTPUTS"] = int(item.split("#")[1])
            if "epochs" in item:
                MODELS[Model]["EPOCHS"] = int(item.split("#")[1])
            if "batch" in item:
                MODELS[Model]["BATCH_SIZE"] = int(item.split("#")[1])
            if "image_count" in item:
                MODELS[Model]["IMAGE_COUNT"] = int(item.split("#")[1])
            if "training_time" in item:
                MODELS[Model]["TRAINING_TIME"] = item.split("#")[1]
            if "training_date" in item:
                MODELS[Model]["TRAINING_DATE"] = item.split("#")[1]
    except:
        SendCrashReport("PyTorch - Error in function GetProperties.", str(traceback.format_exc()))