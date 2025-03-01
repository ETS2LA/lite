from multiprocessing import shared_memory
from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import multiprocessing
import traceback
import pickle
import time


def Initialize():
    global MAIN_SHARED_MEMORY
    global MAIN_LOCK
    MAIN_SHARED_MEMORY = shared_memory.SharedMemory(create=True, size=variables.SharedMemorySize)
    MAIN_LOCK = multiprocessing.Lock()


def AddToQueue(DATA):
    if DATA is not None and str(DATA) not in str(variables.Queue) and "POPUP" not in str(variables.Queue):
        variables.Queue.append(DATA)


def PluginProcessFunction(PluginName, MAIN_SHARED_MEMORY_NAME, MAIN_LOCK, SHARED_MEMORY_NAME, LOCK, DEVMODE):
    try:
        variables.DevelopmentMode = DEVMODE
        global SHARED_MEMORY
        MAIN_SHARED_MEMORY = shared_memory.SharedMemory(name=MAIN_SHARED_MEMORY_NAME)
        SHARED_MEMORY = shared_memory.SharedMemory(name=SHARED_MEMORY_NAME)
        LAST_MEMORY_UPDATE = 0
        DATA_REFRESH_RATE = 100
        LAST_DATA = {}
        Plugin = __import__(f"plugins.{PluginName}.main", fromlist=[""])
        if Plugin.Initialize() == False:
            variables.Break = True
        with LOCK:
            DATA = variables.Queue
            DataBytes = pickle.dumps(DATA)
            if len(DataBytes) > variables.SharedMemorySize:
                SendCrashReport(f"{PluginName} exceeded the shared memory size limit of {variables.SharedMemorySize} bytes.", f"Data: {DATA}\nSize: {len(DataBytes)}")
                while True:
                    variables.Queue.pop(0)
                    if len(DataBytes) <= variables.SharedMemorySize:
                        break
            SHARED_MEMORY.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes
        variables.Queue = []
        while variables.Break == False:
            START = time.time()

            if LAST_MEMORY_UPDATE + 1/DATA_REFRESH_RATE < time.time():
                LAST_MEMORY_UPDATE = time.time()
                UPDATE_MEMORY = True
            else:
                UPDATE_MEMORY = False

            if UPDATE_MEMORY:
                with MAIN_LOCK:
                    DataBytes = bytes(MAIN_SHARED_MEMORY.buf[:variables.SharedMemorySize]).rstrip(b'\x00')
                    if DataBytes:
                        DATA = pickle.loads(DataBytes)
                    else:
                        DATA = {}
                    LAST_DATA = DATA
            else:
                DATA = LAST_DATA

            DATA = Plugin.Run(DATA)
            if DATA is None:
                DATA = {}
            AddToQueue({"DATA": [PluginName, DATA]})

            if UPDATE_MEMORY:
                with LOCK:
                    DATA = variables.Queue
                    DataBytes = pickle.dumps(DATA)
                    if len(DataBytes) > variables.SharedMemorySize:
                        SendCrashReport(f"{PluginName} exceeded the shared memory size limit of {variables.SharedMemorySize} bytes.", f"Data: {DATA}\nSize: {len(DataBytes)}")
                        while True:
                            variables.Queue.pop(0)
                            if len(DataBytes) <= variables.SharedMemorySize:
                                break
                    SHARED_MEMORY.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes

                variables.Queue = []

            TIME_TO_SLEEP = 1/1000 - (time.time() - START)
            if TIME_TO_SLEEP > 0:
                time.sleep(TIME_TO_SLEEP)

    except:
        SendCrashReport(f"Error in plugin {PluginName}.", str(traceback.format_exc()))


def ManagePlugins(Plugin=None, Action=None):
    if Action == None:
        return
    variables.Data = {}
    if Plugin != None and Plugin != "All":
        if Plugin not in variables.AvailablePlugins:
            return
        Plugins = [Plugin]
        if Action != "Stop":
            variables.Popup = [f"{Action}ing {Plugin}...", 0, 0.5]
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
            SHARED_MEMORY = shared_memory.SharedMemory(create=True, size=variables.SharedMemorySize)
            LOCK = multiprocessing.Lock()
            variables.PluginProcesses[Plugin] = multiprocessing.Process(
                target=PluginProcessFunction,
                args=(Plugin, MAIN_SHARED_MEMORY.name, MAIN_LOCK, SHARED_MEMORY.name, LOCK, variables.DevelopmentMode),
                name=Plugin,
                daemon=True
            )
            variables.PluginProcesses[Plugin].start()
            variables.SharedMemories[Plugin] = SHARED_MEMORY
            variables.Locks[Plugin] = LOCK


def ManageSharedMemory():
    for Plugin in variables.AvailablePlugins:
        if Plugin in variables.SharedMemories:
            with variables.Locks[Plugin]:
                DataBytes = bytes(variables.SharedMemories[Plugin].buf[:variables.SharedMemorySize]).rstrip(b'\x00')
                if DataBytes:
                    for Data in pickle.loads(DataBytes):
                        if "DATA" in Data:
                            variables.Data[Data["DATA"][0]] = Data["DATA"][1]
                        elif "POPUP" in Data:
                            variables.Popup = Data["POPUP"]
                        elif "MANAGEPLUGINS" in Data:
                            ManagePlugins(Plugin=Data["MANAGEPLUGINS"][0], Action=Data["MANAGEPLUGINS"][1])
    with MAIN_LOCK:
        Data = variables.Data
        DataBytes = pickle.dumps(Data)
        if len(DataBytes) > variables.SharedMemorySize:
            SendCrashReport(f"Main exceeded the shared memory size limit of {variables.SharedMemorySize} bytes.", f"Data: {Data}\nSize: {len(DataBytes)}")
        MAIN_SHARED_MEMORY.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes