from src.server import SendCrashReport
import src.variables as variables
import src.settings as settings
import multiprocessing
import traceback


def PluginProcessFunction(PluginName, Queue, DataQueue):
    variables.QUEUE = Queue
    Plugin = __import__(f"plugins.{PluginName}.main", fromlist=[""])
    Plugin.Initialize()
    while variables.BREAK == False:
        try:
            DATA = Plugin.Run(DataQueue.get())
            if DATA != None:
                variables.QUEUE.put({"DATA": [PluginName, DATA]})
            while variables.QUEUE.empty() == False:
                Queue.put(variables.QUEUE.get())
        except:
            SendCrashReport(f"Error in plugin {PluginName}.", str(traceback.format_exc()))


def ManagePlugins(Plugin=None, Action=None):
    if Action == None:
        return
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
            variables.PLUGIN_PROCESSES[Plugin].terminate()
            del variables.PLUGIN_PROCESSES[Plugin]

        if Action == "Start" or Action == "Restart":
            variables.PLUGIN_PROCESSES[Plugin] = multiprocessing.Process(target=PluginProcessFunction, args=(Plugin, variables.PLUGIN_QUEUE, variables.DATA_QUEUE), name=Plugin, daemon=True)
            variables.PLUGIN_PROCESSES[Plugin].start()


def ManageQueues():
    if variables.PLUGIN_QUEUE.empty() == False:
        while variables.PLUGIN_QUEUE.empty() == False:
            Dict = variables.PLUGIN_QUEUE.get()
            if "DATA" in Dict:
                variables.DATA[Dict["DATA"][0]] = Dict["DATA"][1]
            elif "POPUP" in Dict:
                variables.POPUP = Dict["POPUP"]
            elif "MANAGEPLUGINS" in Dict:
                ManagePlugins(Plugin=Dict["MANAGEPLUGINS"][0], Action=Dict["MANAGEPLUGINS"][1])
    variables.DATA_QUEUE.put(variables.DATA)