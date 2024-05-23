import src.variables as variables
import src.settings as settings
import src.console as console


if settings.Get("Console", "HideConsole", False):
    console.HideConsole()


import plugins.NavigationDetectionAI.main as NavigationDetectionAI
NavigationDetectionAI.Initialize()


while variables.BREAK == False:
    NavigationDetectionAI.plugin()


if settings.Get("Console", "HideConsole", False):
    console.RestoreConsole()