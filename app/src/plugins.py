from multiprocessing import shared_memory
from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import multiprocessing
import traceback
import pickle


def Initialize():
    global MAIN_SHARED_MEMORY
    global MAIN_LOCK
    MAIN_SHARED_MEMORY = shared_memory.SharedMemory(create=True, size=variables.SHARED_MEMORY_SIZE)
    MAIN_LOCK = multiprocessing.Lock()


def PluginProcessFunction(PluginName, MAIN_SHARED_MEMORY_NAME, MAIN_LOCK, SHARED_MEMORY_NAME, LOCK):
    try:
        MAIN_SHARED_MEMORY = shared_memory.SharedMemory(name=MAIN_SHARED_MEMORY_NAME)
        SHARED_MEMORY = shared_memory.SharedMemory(name=SHARED_MEMORY_NAME)
        Plugin = __import__(f"plugins.{PluginName}.main", fromlist=[""])
        Plugin.Initialize()

        while variables.BREAK == False:

            with LOCK:
                DataBytes = bytes(MAIN_SHARED_MEMORY.buf[:variables.SHARED_MEMORY_SIZE]).rstrip(b'\x00')
                if DataBytes:
                    Data = pickle.loads(DataBytes)
                else:
                    Data = None

            DATA = Plugin.Run(Data)

            if DATA != None:
                variables.QUEUE.append({"DATA": [PluginName, DATA]})

            with LOCK:
                Data = variables.QUEUE
                DataBytes = pickle.dumps(Data)
                if len(DataBytes) > variables.SHARED_MEMORY_SIZE:
                    SendCrashReport(f"{PluginName} exceeded the shared memory size limit of {variables.SHARED_MEMORY_SIZE} bytes.", f"Data: {Data}\nSize: {len(DataBytes)}")
                SHARED_MEMORY.buf[:variables.SHARED_MEMORY_SIZE][:len(DataBytes)] = DataBytes

            variables.QUEUE = []

    except:
        SendCrashReport(f"Error in plugin {PluginName}.", str(traceback.format_exc()))


def ManagePlugins(Plugin=None, Action=None):
    if Action == None:
        return
    variables.DATA = {}
    if Plugin != None and Plugin != "All":
        if Plugin not in variables.AVAILABLE_PLUGINS:
            return
        Plugins = [Plugin]
        if Action != "Stop":
            variables.POPUP = [f"{Action}ing {Plugin}...", 0, 0.5]
    else:
        Plugins = [Plugin for Plugin in variables.AVAILABLE_PLUGINS if settings.Get("EnabledPlugins", Plugin, True)]

    for Plugin in Plugins:
        if Action == "Stop" or Action == "Restart":
            if Plugin in variables.PLUGIN_PROCESSES:
                variables.PLUGIN_PROCESSES[Plugin].terminate()
                del variables.PLUGIN_PROCESSES[Plugin]

        if Action == "Start" or Action == "Restart":
            SHARED_MEMORY = shared_memory.SharedMemory(create=True, size=variables.SHARED_MEMORY_SIZE)
            LOCK = multiprocessing.Lock()
            variables.PLUGIN_PROCESSES[Plugin] = multiprocessing.Process(
                target=PluginProcessFunction,
                args=(Plugin, MAIN_SHARED_MEMORY.name, MAIN_LOCK, SHARED_MEMORY.name, LOCK),
                name=Plugin,
                daemon=True
            )
            variables.PLUGIN_PROCESSES[Plugin].start()
            variables.SHARED_MEMORYS[Plugin] = SHARED_MEMORY
            variables.LOCKS[Plugin] = LOCK


def ManageSharedMemory():
    for Plugin in variables.AVAILABLE_PLUGINS:
        if Plugin in variables.SHARED_MEMORYS:
            with variables.LOCKS[Plugin]:
                DataBytes = bytes(variables.SHARED_MEMORYS[Plugin].buf[:variables.SHARED_MEMORY_SIZE]).rstrip(b'\x00')
                if DataBytes:
                    for Data in pickle.loads(DataBytes):
                        if "DATA" in Data:
                            variables.DATA[Data["DATA"][0]] = Data["DATA"][1]
                        elif "POPUP" in Data:
                            variables.POPUP = Data["POPUP"]
                        elif "MANAGEPLUGINS" in Data:
                            ManagePlugins(Plugin=Data["MANAGEPLUGINS"][0], Action=Data["MANAGEPLUGINS"][1])
    with MAIN_LOCK:
        Data = variables.DATA
        DataBytes = pickle.dumps(Data)
        if len(DataBytes) > variables.SHARED_MEMORY_SIZE:
            SendCrashReport(f"Main exceeded the shared memory size limit of {variables.SHARED_MEMORY_SIZE} bytes.", f"Data: {Data}\nSize: {len(DataBytes)}")
        MAIN_SHARED_MEMORY.buf[:variables.SHARED_MEMORY_SIZE][:len(DataBytes)] = DataBytes