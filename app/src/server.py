import src.variables as variables
import src.settings as settings
import src.console as console
import src.plugins as plugins
import multiprocessing
import traceback
import requests
import json
import time
import uuid


AllowCrashReports = settings.Get("CrashReports", "SendCrashReports")
if AllowCrashReports == None:
    variables.Page = "CrashReport"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
NORMAL = "\033[0m"


def SendCrashReport(Type:str, Message:str, Additional=None):
    if Message.strip() == "":
        return
    CurrentTime = time.time()
    console.RestoreConsole()
    try:
        if AllowCrashReports == True and settings.Get("CrashReports", "LastCrashReport", 0) + 300 < CurrentTime:
            settings.Set("CrashReports", "LastCrashReport", CurrentTime)
            Additional = {
                "version": variables.Version + " (ETS2LA-Lite)",
                "os": variables.OS,
                "language": variables.Language,
                "custom": Additional
            }

            JsonData = {
                "type": Type,
                "message": Message,
                "additional": Additional
            }

            Url = 'https://crash.tumppi066.fi/crash'
            Headers = {'Content-Type': 'application/json'}
            Data = json.dumps(JsonData)
            try:
                Response = requests.post(Url, headers=Headers, data=Data)
                if Response.status_code == 200:
                    print(GREEN + "\nCrash report sent successfully!" + NORMAL)
                else:
                    print(RED + f"\nFailed to send crash report (Server responded with {Response.status_code})." + NORMAL)
            except:
                print(RED + f"\nUnexpected error occurred while sending the crash report:{NORMAL}\n{str(str(traceback.format_exc()))}")
        elif AllowCrashReports == False:
            print(YELLOW + "\nCrash detected, but crash reports are disabled in the settings. No report was sent." + NORMAL)
        else:
            print(YELLOW + "\nCrash detected, but the crash report rate limit has been reached. No report was sent." + NORMAL)
    except:
        print(RED + f"\nCrash report sending failed due to an unexpected error:{NORMAL}\n{str(traceback.format_exc())}")
    while Message.endswith('\n'):
        Message = Message[:-1]
    if variables.DevelopmentMode == False:
        Message = f"{RED}>{NORMAL} " + Message.replace("\n", f"\n{RED}>{NORMAL} ")
    print(f"{RED}{Type}{NORMAL}\n{Message}\n")
    ProcessName = multiprocessing.current_process().name
    if ProcessName != "MainProcess":
        while True:
            variables.Queue = []
            plugins.AddToQueue({"Popup": [f"{ProcessName} Crashed!", 0]})
            plugins.ManagePlugins(Plugin=ProcessName, Action="Stop")
            DATA = variables.Queue
            DataBytes = plugins.pickle.dumps(DATA)
            plugins.SharedMemory.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes
            time.sleep(0.1)


def GetUserCount():
    if AllowCrashReports == False:
        variables.UserCount = "Please enable crash reporting to fetch user count."
        return "Please enable crash reporting to fetch user count."

    try:
        Response = requests.get("https://api.ets2la.com/tracking/users", timeout=5).json()
        variables.UserCount = Response["data"]["online"]
        return Response["data"]["online"]
    except:
        variables.UserCount = "Could not get user count."
        return "Could not get user count."


def Ping():
    try:
        User = settings.Get("Server", "PingID", str(uuid.uuid4()))
        LastPing = settings.Get("Server", "LastPing", 0)
        CurrentTime = time.time()
        if LastPing + 119 < CurrentTime:
            settings.Set("Server", "LastPing", CurrentTime)
            requests.get(f"https://api.ets2la.com/tracking/ping/{User}", timeout=5)
    except:
        pass