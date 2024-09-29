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


def Loaded(Model="All"):
    if Model == "All":
        for Model in MODELS:
            if MODELS[Model]["Threaded"] == True:
                if MODELS[Model]["UpdateThread"].is_alive(): return False
                if MODELS[Model]["LoadThread"].is_alive(): return False
    else:
        if MODELS[Model]["Threaded"] == True:
            if MODELS[Model]["UpdateThread"].is_alive(): return False
            if MODELS[Model]["LoadThread"].is_alive(): return False
    return True


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

                ModelFileBroken = False

                try:
                    MODELS[Model]["Metadata"] = {"data": []}
                    MODELS[Model]["Model"] = torch.jit.load(os.path.join(MODELS[Model]["Path"], GetName(Model)), _extra_files=MODELS[Model]["Metadata"], map_location=MODELS[Model]["Device"])
                    MODELS[Model]["Model"].eval()
                    MODELS[Model]["Metadata"] = eval(MODELS[Model]["Metadata"]["data"])
                    for Item in MODELS[Model]["Metadata"]:
                        Item = str(Item)
                        if "image_width" in Item:
                            MODELS[Model]["IMG_WIDTH"] = int(Item.split("#")[1])
                        if "image_height" in Item:
                            MODELS[Model]["IMG_HEIGHT"] = int(Item.split("#")[1])
                        if "image_channels" in Item:
                            MODELS[Model]["IMG_CHANNELS"] = str(Item.split("#")[1])
                        if "outputs" in Item:
                            MODELS[Model]["OUTPUTS"] = int(Item.split("#")[1])
                        if "epochs" in Item:
                            MODELS[Model]["EPOCHS"] = int(Item.split("#")[1])
                        if "batch" in Item:
                            MODELS[Model]["BATCH_SIZE"] = int(Item.split("#")[1])
                        if "image_count" in Item:
                            MODELS[Model]["IMAGE_COUNT"] = int(Item.split("#")[1])
                        if "training_time" in Item:
                            MODELS[Model]["TRAINING_TIME"] = Item.split("#")[1]
                        if "training_date" in Item:
                            MODELS[Model]["TRAINING_DATE"] = Item.split("#")[1]
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
                    Response = requests.get("https://huggingface.co/", timeout=3)
                    Response = Response.status_code
                except requests.exceptions.RequestException:
                    Response = None

                if Response == 200:
                    plugins.AddToQueue({"POPUP": ["Checking for model updates...", 0, 0.5]})
                    print(DARK_GREY + f"[{Model}] " + GREEN + "Checking for model updates..." + NORMAL)

                    if settings.Get("PyTorch", f"{Model}-LastUpdateCheck", 0) + 600 > time.time():
                        if settings.Get("PyTorch", f"{Model}-LatestModel", "unset") == GetName(Model):
                            print(DARK_GREY + f"[{Model}] " + GREEN + "No model updates available!" + NORMAL)
                            return

                    Url = f'https://huggingface.co/{MODELS[Model]["ModelOwner"]}/{Model}/tree/main/model'
                    Response = requests.get(Url)
                    Soup = BeautifulSoup(Response.content, 'html.parser')

                    LatestModel = None
                    for Link in Soup.find_all("a", href=True):
                        HREF = Link["href"]
                        if HREF.startswith(f'/{MODELS[Model]["ModelOwner"]}/{Model}/blob/main/model'):
                            LatestModel = HREF.split("/")[-1]
                            settings.Set("PyTorch", f"{Model}-LatestModel", LatestModel)
                            break
                    if LatestModel == None:
                        LatestModel = settings.Get("PyTorch", f"{Model}-LatestModel", "unset")

                    CurrentModel = GetName(Model)

                    if str(LatestModel) != str(CurrentModel):
                        plugins.AddToQueue({"POPUP": ["Updating the model...", 0, 0.5]})
                        print(DARK_GREY + f"[{Model}] " + GREEN + "Updating the model..." + NORMAL)
                        Delete(Model)
                        Response = requests.get(f'https://huggingface.co/{MODELS[Model]["ModelOwner"]}/{Model}/resolve/main/model/{LatestModel}?download=true', stream=True)
                        with open(os.path.join(MODELS[Model]["Path"], f"{LatestModel}"), "wb") as ModelFile:
                            TotalSize = int(Response.headers.get('content-length', 0))
                            DownloadedSize = 0
                            ChunkSize = 1024
                            for Data in Response.iter_content(chunk_size=ChunkSize):
                                DownloadedSize += len(Data)
                                ModelFile.write(Data)
                                Progress = round((DownloadedSize / TotalSize) * 100)
                                plugins.AddToQueue({"POPUP": [f"Downloading the model: {Progress}%", Progress, 0.5]})
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
        for File in os.listdir(MODELS[Model]["Path"]):
            if File.endswith(".pt"):
                return File
        return None
    except:
        SendCrashReport("PyTorch - Error in function GetName.", str(traceback.format_exc()))
        return None


def Delete(Model):
    try:
        FolderExists(Model)
        for File in os.listdir(MODELS[Model]["Path"]):
            if File.endswith(".pt"):
                os.remove(os.path.join(MODELS[Model]["Path"], File))
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