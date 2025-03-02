from multiprocessing import shared_memory
from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
from src.ui import Popup
import multiprocessing
import traceback
import pickle
import time


def Initialize():
    global MainSharedMemory
    global MainLock
    MainSharedMemory = shared_memory.SharedMemory(create=True, size=variables.SharedMemorySize)
    MainLock = multiprocessing.Lock()


def AddToQueue(Data):
    if Data is not None and str(Data) not in str(variables.Queue) and "Popup" not in str(variables.Queue):
        variables.Queue.append(Data)


def PluginProcessFunction(PluginName, MainSharedMemoryName, MainLock, SharedMemoryName, Lock, DEVMODE):
    try:
        variables.DevelopmentMode = DEVMODE
        global SharedMemory
        MainSharedMemory = shared_memory.SharedMemory(name=MainSharedMemoryName)
        SharedMemory = shared_memory.SharedMemory(name=SharedMemoryName)
        LastMemoryUpdate = 0
        DataRefreshRate = 100
        LastData = {}
        Plugin = __import__(f"plugins.{PluginName}.main", fromlist=[""])
        if Plugin.Initialize() == False:
            variables.Break = True
        with Lock:
            Data = variables.Queue
            DataBytes = pickle.dumps(Data)
            if len(DataBytes) > variables.SharedMemorySize:
                SendCrashReport(f"{PluginName} exceeded the shared memory size limit of {variables.SharedMemorySize} bytes.", f"Data: {Data}\nSize: {len(DataBytes)}")
                while True:
                    variables.Queue.pop(0)
                    if len(DataBytes) <= variables.SharedMemorySize:
                        break
            SharedMemory.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes
        variables.Queue = []
        while variables.Break == False:
            Start = time.time()

            if LastMemoryUpdate + 1/DataRefreshRate < time.time():
                LastMemoryUpdate = time.time()
                UpdateMemory = True
            else:
                UpdateMemory = False

            if UpdateMemory:
                with MainLock:
                    DataBytes = bytes(MainSharedMemory.buf[:variables.SharedMemorySize]).rstrip(b'\x00')
                    if DataBytes:
                        Data = pickle.loads(DataBytes)
                    else:
                        Data = {}
                    LastData = Data
            else:
                Data = LastData

            Data = Plugin.Run(Data)
            if Data is None:
                Data = {}
            AddToQueue({"DATA": [PluginName, Data]})

            if UpdateMemory:
                with Lock:
                    Data = variables.Queue
                    DataBytes = pickle.dumps(Data)
                    if len(DataBytes) > variables.SharedMemorySize:
                        SendCrashReport(f"{PluginName} exceeded the shared memory size limit of {variables.SharedMemorySize} bytes.", f"Data: {Data}\nSize: {len(DataBytes)}")
                        while True:
                            variables.Queue.pop(0)
                            if len(DataBytes) <= variables.SharedMemorySize:
                                break
                    SharedMemory.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes

                variables.Queue = []

            TimeToSleep = 1/1000 - (time.time() - Start)
            if TimeToSleep > 0:
                time.sleep(TimeToSleep)

    except:
        SendCrashReport(f"Error in plugin {PluginName}.", str(traceback.format_exc()))


def ManagePlugins(Plugin=None, Action=None):
    """
    Start, Stop or Restart all or a specific plugin(s).

    Parameters
    ----------
    Plugin : str
        The plugin name. Can also be `All`.
    Action : str
        `Start`, `Stop` or `Restart` the plugin(s).	

    Returns
    -------
    None
    """
    if multiprocessing.current_process().name != "MainProcess":
        AddToQueue({"ManagePlugins": [Plugin, Action]})
        return

    if Action == None:
        return

    variables.Data = {}

    if Plugin != None and Plugin != "All":
        if Plugin not in variables.AvailablePlugins:
            return
        Plugins = [Plugin]
        if Action != "Stop":
            Popup(Text=f"{Action}ing {Plugin}...", Progress=0)
            
    else:
        Plugins = [Plugin for Plugin in variables.AvailablePlugins if settings.Get("Plugins", Plugin, False)]

    for Plugin in Plugins:
        if Action == "Stop" or Action == "Restart":
            if Plugin in variables.PluginProcesses:
                variables.PluginProcesses[Plugin].terminate()
                del variables.PluginProcesses[Plugin]
                variables.SharedMemories[Plugin].close()
                del variables.SharedMemories[Plugin]

        if Action == "Start" or Action == "Restart":
            SharedMemory = shared_memory.SharedMemory(create=True, size=variables.SharedMemorySize)
            Lock = multiprocessing.Lock()
            variables.PluginProcesses[Plugin] = multiprocessing.Process(
                target=PluginProcessFunction,
                args=(Plugin, MainSharedMemory.name, MainLock, SharedMemory.name, Lock, variables.DevelopmentMode),
                name=Plugin,
                daemon=True
            )
            variables.PluginProcesses[Plugin].start()
            variables.SharedMemories[Plugin] = SharedMemory
            variables.Locks[Plugin] = Lock


def ManageSharedMemory():
    for Plugin in variables.AvailablePlugins:
        if Plugin in variables.SharedMemories:
            with variables.Locks[Plugin]:
                DataBytes = bytes(variables.SharedMemories[Plugin].buf[:variables.SharedMemorySize]).rstrip(b'\x00')
                if DataBytes:
                    for Data in pickle.loads(DataBytes):
                        if "DATA" in Data:
                            variables.Data[Data["DATA"][0]] = Data["DATA"][1]
                        elif "Popup" in Data:
                            Popup(Data["Popup"][0], Data["Popup"][1])
                        elif "ManagePlugins" in Data:
                            ManagePlugins(Plugin=Data["ManagePlugins"][0], Action=Data["ManagePlugins"][1])
    with MainLock:
        Data = variables.Data
        DataBytes = pickle.dumps(Data)
        if len(DataBytes) > variables.SharedMemorySize:
            SendCrashReport(f"Main exceeded the shared memory size limit of {variables.SharedMemorySize} bytes.", f"Data: {Data}\nSize: {len(DataBytes)}")
        MainSharedMemory.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes