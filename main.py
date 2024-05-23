import src.variables as variables
import src.settings as settings
import src.console as console


if settings.Get("Console", "HideConsole", False):
    console.HideConsole()

if settings.Get("Console", "HideConsole", False):
    console.RestoreConsole()