from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import src.console as console
from bs4 import BeautifulSoup
import src.ui as ui
import subprocess
import threading
import traceback
import requests
import GPUtil
import psutil
import numpy
import time
import cv2
import sys
import os

try:
    from torchvision import transforms
    import torch
    TorchAvailable = True
except:
    TorchAvailable = False
    SendCrashReport("PyTorch - PyTorch import error.", str(traceback.format_exc()))


RED = "\033[91m"
GREEN = "\033[92m"
GRAY = "\033[90m"
YELLOW = "\033[93m"
NORMAL = "\033[0m"


def Popup(Text="", Progress=0):
    ui.Popup(Text=Text, Progress=Progress)


def InstallCUDA():
    try:
        def InstallCUDAThread():
            try:
                Command = ["cmd", "/c", f"{variables.Path}python/python.exe -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126 --progress-bar raw --force-reinstall"]
                Process = subprocess.Popen(Command, cwd=variables.Path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                with open(LockFilePath, "w") as File:
                    File.write(str(Process.pid))
                    File.close()
                while psutil.pid_exists(Process.pid):
                    time.sleep(0.1)
                    Output = Process.stdout.readline()
                    Output = str(Output.decode().strip()).replace("Progress ", "").split(" of ")
                    if len(Output) == 2:
                        TotalSize = Output[1]
                        DownloadedSize = Output[0]
                        try:
                            Popup(Text=f"Installing CUDA: {round((int(DownloadedSize) / int(TotalSize)) * 100)}%", Progress=(int(DownloadedSize) / int(TotalSize)) * 100)
                        except:
                            Popup(Text="Installing CUDA...", Progress=-1)
                    else:
                        Popup(Text="Installing CUDA...", Progress=-1)
                if os.path.exists(LockFilePath):
                    os.remove(LockFilePath)
                print(GREEN + "CUDA installation completed." + NORMAL)
                Popup(Text="CUDA installation completed.", Progress=0)
                ui.Restart()
            except:
                SendCrashReport("PyTorch - Error in function InstallCUDAThread.", str(traceback.format_exc()))
        print(GREEN + "Installing CUDA..." + NORMAL)
        Popup(Text="Installing CUDA...", Progress=-1)
        LockFilePath = f"{variables.Path}cache/CUDAInstall.txt"
        if os.path.exists(LockFilePath):
            with open(LockFilePath, "r") as File:
                PID = int(File.read().strip())
                File.close()
            if str(PID) in str(psutil.pids()):
                print(RED + "CUDA is already being installed." + NORMAL)
                Popup(Text="CUDA is already being installed.", Progress=0)
                return
        threading.Thread(target=InstallCUDAThread, daemon=True).start()
    except:
        SendCrashReport("PyTorch - Error in function InstallCUDA.", str(traceback.format_exc()))


def UninstallCUDA():
    try:
        def UninstallCUDAThread():
            try:
                Command = ["cmd", "/c", f"{variables.Path}python/python.exe -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --progress-bar raw --force-reinstall"]
                Process = subprocess.Popen(Command, cwd=variables.Path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                with open(LockFilePath, "w") as File:
                    File.write(str(Process.pid))
                    File.close()
                while psutil.pid_exists(Process.pid):
                    time.sleep(0.1)
                    Output = Process.stdout.readline()
                    Output = str(Output.decode().strip()).replace("Progress ", "").split(" of ")
                    if len(Output) == 2:
                        TotalSize = Output[1]
                        DownloadedSize = Output[0]
                        try:
                            Popup(Text=f"Uninstalling CUDA: {round((int(DownloadedSize) / int(TotalSize)) * 100)}%", Progress=(int(DownloadedSize) / int(TotalSize)) * 100)
                        except:
                            Popup(Text="Uninstalling CUDA...", Progress=-1)
                    else:
                        Popup(Text="Uninstalling CUDA...", Progress=-1)
                if os.path.exists(LockFilePath):
                    os.remove(LockFilePath)
                print(GREEN + "CUDA uninstallation completed." + NORMAL)
                Popup(Text="CUDA uninstallation completed.", Progress=0)
                ui.Restart()
            except:
                SendCrashReport("PyTorch - Error in function UninstallCUDAThread.", str(traceback.format_exc()))
        print(GREEN + "Uninstalling CUDA..." + NORMAL)
        Popup(Text="Uninstalling CUDA...", Progress=-1)
        LockFilePath = f"{variables.Path}cache/CUDAInstall.txt"
        if os.path.exists(LockFilePath):
            with open(LockFilePath, "r") as File:
                PID = int(File.read().strip())
                File.close()
            if str(PID) in str(psutil.pids()):
                print(RED + "CUDA is already being uninstalled." + NORMAL)
                Popup(Text="CUDA is already being uninstalled.", Progress=0)
                return
        threading.Thread(target=UninstallCUDAThread, daemon=True).start()
    except:
        SendCrashReport("PyTorch - Error in function UninstallCUDA.", str(traceback.format_exc()))


def CheckCUDA():
    try:
        variables.CUDAInstalled = "Loading..."
        variables.CUDAAvailable = "Loading..."
        variables.CUDACompatible = "Loading..."
        variables.CUDADetails = "Loading..."
        def CheckCUDAThread():
            try:
                Result = subprocess.run(f"{variables.Path}python/python.exe -m pip list", shell=True, capture_output=True, text=True)
                Modules = Result.stdout
                CUDAInstalled = True
                PyTorchModules = []
                for Module in Modules.splitlines():
                    if "torch " in Module:
                        PyTorchModules.append(Module)
                        if "cu" not in Module:
                            CUDAInstalled = False
                    elif "torchvision " in Module:
                        PyTorchModules.append(Module)
                        if "cu" not in Module:
                            CUDAInstalled = False
                    elif "torchaudio " in Module:
                        PyTorchModules.append(Module)
                        if "cu" not in Module:
                            CUDAInstalled = False
                GPUs = [str(GPU.name) for GPU in GPUtil.getGPUs()]
                variables.CUDAInstalled = CUDAInstalled
                variables.CUDAAvailable = torch.cuda.is_available()
                variables.CUDACompatible = ("nvidia" in str([GPU.lower() for GPU in GPUs]))
                variables.CUDADetails = "\n".join(PyTorchModules) + "\n" + "\n".join([str(GPU.name).upper() for GPU in GPUtil.getGPUs()] if len(GPUs) > 0 else ["No GPUs found."])
            except:
                SendCrashReport("PyTorch - Error in function CheckCUDAThread.", str(traceback.format_exc()))
        threading.Thread(target=CheckCUDAThread, daemon=True).start()
    except:
        SendCrashReport("PyTorch - Error in function CheckCUDA.", str(traceback.format_exc()))


class Model:
    def __init__(Self, HuggingFaceOwner:str, HuggingFaceRepository:str, HuggingFaceModelFolder:str, DType:torch.dtype=torch.bfloat16, Threaded:bool=True):
        Self.DType = DType
        Self.Device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        Self.Path = f"{variables.Path}cache/{HuggingFaceOwner}/{HuggingFaceRepository}/{HuggingFaceModelFolder}"

        Self.HuggingFaceOwner = str(HuggingFaceOwner)
        Self.HuggingFaceRepository = str(HuggingFaceRepository)
        Self.HuggingFaceModelFolder = str(HuggingFaceModelFolder)

        Self.Identifier = f"{HuggingFaceRepository}/{HuggingFaceModelFolder}"

        Self.Threaded = Threaded

        Self.UpdateThread:threading.Thread
        Self.LoadThread:threading.Thread
        Self.Loaded:bool = False

        Self.Metadata:dict
        Self.Model:torch.jit.ScriptModule

        Self.ImageWidth:int
        Self.ImageHeight:int
        Self.ColorChannels:int
        Self.ColorChannelsStr:str
        Self.Outputs:int
        Self.TrainingTime:str
        Self.TrainingDate:str


    def Detect(Self, Image:numpy.ndarray):
        try:
            if len(Image.shape) == 3:
                if Image.shape[2] == 1 and Self.ColorChannels == 3:
                    Image = cv2.cvtColor(Image, cv2.COLOR_GRAY2RGB)
                elif Image.shape[2] == 3 and Self.ColorChannels == 1:
                    Image = cv2.cvtColor(Image, cv2.COLOR_RGB2GRAY)
                elif Image.shape[2] == 4 and Self.ColorChannels == 3:
                    Image = cv2.cvtColor(Image, cv2.COLOR_RGBA2RGB)
                elif Image.shape[2] == 4 and Self.ColorChannels == 1:
                    Image = cv2.cvtColor(Image, cv2.COLOR_RGBA2GRAY)
            elif len(Image.shape) == 2:
                if Self.ColorChannels == 3:
                    Image = cv2.cvtColor(Image, cv2.COLOR_GRAY2RGB)
            Image = cv2.resize(Image, (Self.ImageWidth, Self.ImageHeight))
            if Image.dtype == numpy.uint8:
                Image = numpy.array(Image, dtype=numpy.float32) / 255.0
            Image = torch.as_tensor(transforms.ToTensor()(Image).unsqueeze(0), dtype=Self.DType, device=Self.Device)
            with torch.no_grad():
                Output = Self.Model(Image)
                Output = Output.tolist()
            return Output
        except:
            SendCrashReport("PyTorch - Error in function Detect.", str(traceback.format_exc()))


    def Load(Self):
        try:
            def LoadFunction():
                try:
                    Self.CheckForUpdates()
                    while Self.UpdateThread.is_alive():
                        time.sleep(0.1)

                    if Self.GetName() == None:
                        return

                    Popup(Text="Loading the model...", Progress=0)
                    print(GRAY + f"[{Self.Identifier}] " + GREEN + "Loading the model..." + NORMAL)

                    ModelFileBroken = False

                    try:
                        Self.Metadata = {"data": [], "Data": [], "metadata": [], "Metadata": []}
                        Self.Model = torch.jit.load(os.path.join(Self.Path, Self.GetName()), _extra_files=Self.Metadata, map_location=Self.Device)
                        Self.Model.eval()
                        Self.Model.to(Self.DType)
                        Key = max(Self.Metadata, key=lambda Key: len(Self.Metadata[Key]))
                        Self.Metadata = eval(Self.Metadata[Key])
                        for Item in Self.Metadata:
                            try:
                                Item = str(Item)
                                if "image_width" in Item or "ImageWidth" in Item:
                                    Self.ImageWidth = int(Item.split("#")[1])
                                if "image_height" in Item or "ImageHeight" in Item:
                                    Self.ImageHeight = int(Item.split("#")[1])
                                if "image_channels" in Item or "ImageChannels" in Item:
                                    Data = Item.split("#")[1]
                                    try:
                                        Self.ColorChannels = int(Data)
                                    except ValueError:
                                        Self.ColorChannelsStr = str(Data)
                                if "color_channels" in Item or "ColorChannels" in Item:
                                    Data = Item.split("#")[1]
                                    try:
                                        Self.ColorChannels = int(Data)
                                    except ValueError:
                                        Self.ColorChannelsStr = str(Data)
                                if "outputs" in Item or "Outputs" in Item:
                                    Self.Outputs = int(Item.split("#")[1])
                                if "training_time" in Item or "TrainingTime" in Item:
                                    Self.TrainingTime = Item.split("#")[1]
                                if "training_date" in Item or "TrainingDate" in Item:
                                    Self.TrainingDate = Item.split("#")[1]
                            except:
                                try:
                                    print(GRAY + f"[{Self.Identifier}] " + YELLOW + f"> Unable to parse '{Item.split('#')[0]}' from model metadata!" + NORMAL)
                                except:
                                    print(GRAY + f"[{Self.Identifier}] " + YELLOW + f"> Unable to parse an item from model metadata!" + NORMAL)
                    except:
                        ModelFileBroken = True

                    if ModelFileBroken == False:
                        Popup(Text="Successfully loaded the model!", Progress=100)
                        print(GRAY + f"[{Self.Identifier}] " + GREEN + "Successfully loaded the model!" + NORMAL)
                        Self.Loaded = True
                    else:
                        Popup(Text="Failed to load the model because the model file is broken.", Progress=0)
                        print(GRAY + f"[{Self.Identifier}] " + RED + "Failed to load the model because the model file is broken." + NORMAL)
                        Self.Loaded = False
                        Self.HandleBroken()
                except:
                    SendCrashReport("PyTorch - Loading Error.", str(traceback.format_exc()))
                    Popup(Text="Failed to load the model!", Progress=0)
                    print(GRAY + f"[{Self.Identifier}] " + RED + "Failed to load the model!" + NORMAL)
                    Self.Loaded = False

            if TorchAvailable:
                if Self.Threaded:
                    Self.LoadThread = threading.Thread(target=LoadFunction, daemon=True)
                    Self.LoadThread.start()
                else:
                    LoadFunction()

        except:
            SendCrashReport("PyTorch - Error in function Load.", str(traceback.format_exc()))
            Popup(Text="Failed to load the model.", Progress=0)
            print(GRAY + f"[{Self.Identifier}] " + RED + "Failed to load the model." + NORMAL)


    def CheckForUpdates(Self):
        try:
            def CheckForUpdatesFunction():
                try:

                    if "--dev" in sys.argv:
                        if Self.GetName() != None:
                            print(GRAY + f"[{Self.Identifier}] " + YELLOW + "Development mode enabled, skipping update check..." + NORMAL)
                            return
                        else:
                            print(GRAY + f"[{Self.Identifier}] " + YELLOW + "Development mode enabled, downloading model because it doesn't exist..." + NORMAL)

                    Popup(Text="Checking for model updates...", Progress=0)
                    print(GRAY + f"[{Self.Identifier}] " + GREEN + "Checking for model updates..." + NORMAL)

                    if settings.Get("PyTorch", f"{Self.Identifier}-LastUpdateCheck", 0) + 600 > time.time():
                        if settings.Get("PyTorch", f"{Self.Identifier}-LatestModel", "unset") == Self.GetName():
                            print(GRAY + f"[{Self.Identifier}] " + GREEN + "No model updates available!" + NORMAL)
                            return

                    try:
                        HuggingFaceResponse = requests.get("https://huggingface.co/", timeout=3)
                        HuggingFaceResponse = HuggingFaceResponse.status_code
                        ETS2LAResponse = None
                    except:
                        try:
                            ETS2LAResponse = requests.get("https://cdn.ets2la.com/", timeout=3)
                            ETS2LAResponse = ETS2LAResponse.status_code
                            HuggingFaceResponse = None
                            print(GRAY + f"[{Self.Identifier}] " + GREEN + "Using cdn.ets2la.com..." + NORMAL)
                        except:
                            HuggingFaceResponse = None
                            ETS2LAResponse = None

                    if HuggingFaceResponse == 200:
                        Url = f'https://huggingface.co/{Self.HuggingFaceOwner}/{Self.HuggingFaceRepository}/tree/main/{Self.HuggingFaceModelFolder}'
                        Response = requests.get(Url)
                        Soup = BeautifulSoup(Response.content, 'html.parser')

                        LatestModel = None
                        for Link in Soup.find_all("a", href=True):
                            HREF = Link["href"]
                            if HREF.startswith(f'/{Self.HuggingFaceOwner}/{Self.HuggingFaceRepository}/blob/main/{Self.HuggingFaceModelFolder}'):
                                LatestModel = HREF.split("/")[-1]
                                settings.Set("PyTorch", f"{Self.Identifier}-LatestModel", LatestModel)
                                break
                        if LatestModel == None:
                            LatestModel = settings.Get("PyTorch", f"{Self.Identifier}-LatestModel", "unset")

                        CurrentModel = Self.GetName()

                        if str(LatestModel) != str(CurrentModel):
                            Popup(Text="Updating the model...", Progress=0)
                            print(GRAY + f"[{Self.Identifier}] " + GREEN + "Updating the model..." + NORMAL)
                            Self.Delete()
                            StartTime = time.time()
                            Response = requests.get(f'https://huggingface.co/{Self.HuggingFaceOwner}/{Self.HuggingFaceRepository}/resolve/main/{Self.HuggingFaceModelFolder}/{LatestModel}?download=true', stream=True, timeout=15)
                            with open(os.path.join(Self.Path, f"{LatestModel}"), "wb") as ModelFile:
                                TotalSize = int(Response.headers.get('content-length', 1))
                                DownloadedSize = 0
                                ChunkSize = 1024
                                for Data in Response.iter_content(chunk_size=ChunkSize):
                                    DownloadedSize += len(Data)
                                    ModelFile.write(Data)
                                    Progress = (DownloadedSize / TotalSize) * 100
                                    ETA = time.strftime('%H:%M:%S' if (time.time() - StartTime) / Progress * (100 - Progress) >= 3600 else '%M:%S', time.gmtime((time.time() - StartTime) / Progress * (100 - Progress)))
                                    Popup(Text=f"Downloading the model: {round(Progress)}% - ETA: {ETA}", Progress=Progress)
                            Popup(Text="Successfully updated the model!", Progress=100)
                            print(GRAY + f"[{Self.Identifier}] " + GREEN + "Successfully updated the model!" + NORMAL)
                        else:
                            Popup(Text="No model updates available!", Progress=100)
                            print(GRAY + f"[{Self.Identifier}] " + GREEN + "No model updates available!" + NORMAL)
                        settings.Set("PyTorch", f"{Self.Identifier}-LastUpdateCheck", time.time())

                    elif ETS2LAResponse == 200:
                        Url = f'https://cdn.ets2la.com/models/{Self.HuggingFaceOwner}/{Self.HuggingFaceRepository}/{Self.HuggingFaceModelFolder}'
                        Response = requests.get(Url).json()

                        LatestModel = None
                        if "success" in Response:
                            LatestModel = Response["success"]
                            settings.Set("PyTorch", f"{Self.Identifier}-LatestModel", LatestModel)
                        if LatestModel == None:
                            LatestModel = settings.Get("PyTorch", f"{Self.Identifier}-LatestModel", "unset")

                        CurrentModel = Self.GetName()

                        if str(LatestModel) != str(CurrentModel):
                            Popup(Text="Updating the model...", Progress=0)
                            print(GRAY + f"[{Self.Identifier}] " + GREEN + "Updating the model..." + NORMAL)
                            Self.Delete()
                            StartTime = time.time()
                            Response = requests.get(f'https://cdn.ets2la.com/models/{Self.HuggingFaceOwner}/{Self.HuggingFaceRepository}/{Self.HuggingFaceModelFolder}/download', stream=True, timeout=15)
                            with open(os.path.join(Self.Path, f"{LatestModel}"), "wb") as ModelFile:
                                TotalSize = int(Response.headers.get('content-length', 1))
                                DownloadedSize = 0
                                ChunkSize = 1024
                                for Data in Response.iter_content(chunk_size=ChunkSize):
                                    DownloadedSize += len(Data)
                                    ModelFile.write(Data)
                                    Progress = (DownloadedSize / TotalSize) * 100
                                    ETA = time.strftime('%H:%M:%S' if (time.time() - StartTime) / Progress * (100 - Progress) >= 3600 else '%M:%S', time.gmtime((time.time() - StartTime) / Progress * (100 - Progress)))
                                    Popup(Text=f"Downloading the model: {round(Progress)}% - ETA: {ETA}", Progress=Progress)
                            Popup(Text="Successfully updated the model!", Progress=100)
                            print(GRAY + f"[{Self.Identifier}] " + GREEN + "Successfully updated the model!" + NORMAL)
                        else:
                            Popup(Text="No model updates available!", Progress=100)
                            print(GRAY + f"[{Self.Identifier}] " + GREEN + "No model updates available!" + NORMAL)
                        settings.Set("PyTorch", f"{Self.Identifier}-LastUpdateCheck", time.time())

                    else:

                        console.RestoreConsole()
                        Popup(Text="Connection to 'https://huggingface.co' and 'https://cdn.ets2la.com' is not available. Unable to check for updates.", Progress=0)
                        print(GRAY + f"[{Self.Identifier}] " + RED + "Connection to 'https://huggingface.co' and 'https://cdn.ets2la.com' is not available. Unable to check for updates." + NORMAL)

                except:
                    SendCrashReport("PyTorch - Error in function CheckForUpdatesFunction.", str(traceback.format_exc()))
                    Popup(Text="Failed to check for model updates or update the model.", Progress=0)
                    print(GRAY + f"[{Self.Identifier}] " + RED + "Failed to check for model updates or update the model." + NORMAL)

            if Self.Threaded:
                Self.UpdateThread = threading.Thread(target=CheckForUpdatesFunction, daemon=True)
                Self.UpdateThread.start()
            else:
                CheckForUpdatesFunction()

        except:
            SendCrashReport("PyTorch - Error in function CheckForUpdates.", str(traceback.format_exc()))
            Popup(Text="Failed to check for model updates or update the model.", Progress=0)
            print(GRAY + f"[{Self.Identifier}] " + RED + "Failed to check for model updates or update the model." + NORMAL)


    def FolderExists(Self):
        try:
            if os.path.exists(Self.Path) == False:
                os.makedirs(Self.Path)
        except:
            SendCrashReport("PyTorch - Error in function FolderExists.", str(traceback.format_exc()))


    def GetName(Self):
        try:
            Self.FolderExists()
            for File in os.listdir(Self.Path):
                if File.endswith(".pt"):
                    return File
            return None
        except:
            SendCrashReport("PyTorch - Error in function GetName.", str(traceback.format_exc()))
            return None


    def Delete(Self):
        try:
            if "--dev" in sys.argv and os.listdir(Self.Path) != []:
                print(GRAY + f"[{Self.Identifier}] " + YELLOW + "Development mode enabled, skipping model deletion..." + NORMAL)
                return
            Self.FolderExists()
            for File in os.listdir(Self.Path):
                if File.endswith(".pt"):
                    os.remove(os.path.join(Self.Path, File))
        except PermissionError:
            global TorchAvailable
            TorchAvailable = False
            print(GRAY + f"[{Self.Identifier}] " + RED + "PyTorch - PermissionError in function Delete:\n" + NORMAL + str(traceback.format_exc()))
            console.RestoreConsole()
        except:
            SendCrashReport("PyTorch - Error in function Delete.", str(traceback.format_exc()))


    def HandleBroken(Self):
        try:
            if "--dev" in sys.argv:
                print(GRAY + f"[{Self.Identifier}] " + RED + "Can't handle broken models in development mode, all pytorch loader actions paused..." + NORMAL)
                while True: time.sleep(1)
            Self.Delete()
            Self.CheckForUpdates()
            while Self.UpdateThread.is_alive():
                time.sleep(0.1)
            time.sleep(0.5)
            if TorchAvailable == True:
                Self.Load()
        except:
            SendCrashReport("PyTorch - Error in function HandleBroken.", str(traceback.format_exc()))