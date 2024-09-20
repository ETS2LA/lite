import src.variables as variables
import src.settings as settings
import multiprocessing


def PluginProcessFunction(PluginName, Queue):
    variables.QUEUE = Queue
    Plugin = __import__(f"plugins.{PluginName}.main", fromlist=[""])
    Plugin.Initialize()
    while variables.BREAK == False:
        Plugin.plugin()
        while variables.QUEUE.empty() == False:
            Queue.put(variables.QUEUE.get())


def ManagePlugins(Plugin=None, Action=None):
    if Action == None:
        return
    if Plugin != None and Plugin != "All":
        if Plugin not in variables.AVAILABLE_PLUGINS:
            print(f"Plugin {Plugin} not in AVAILABLE_PLUGINS!")
            return
        Plugins = [Plugin]
    else:
        Plugins = [Plugin for Plugin in variables.AVAILABLE_PLUGINS if settings.Get("EnabledPlugins", Plugin, True)]

    for Plugin in Plugins:
        if Action == "Stop" or Action == "Restart":
            variables.PLUGIN_PROCESSES[Plugin].terminate()
            del variables.PLUGIN_PROCESSES[Plugin]

        if Action == "Start" or Action == "Restart":
            variables.PLUGIN_PROCESSES[Plugin] = multiprocessing.Process(target=PluginProcessFunction, args=(Plugin, variables.PLUGIN_QUEUE), name=Plugin, daemon=True)
            variables.PLUGIN_PROCESSES[Plugin].start()


def ManageQueues():
    if variables.PLUGIN_QUEUE.empty() == False:
        variables.POPUP = variables.PLUGIN_QUEUE.get()
        while variables.PLUGIN_QUEUE.empty() == False:
            variables.PLUGIN_QUEUE.get()