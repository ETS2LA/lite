import src.variables as variables
import src.settings as settings
import src.console as console
import multiprocessing
import traceback
import requests
import json
import time


ALLOW_CRASH_REPORTS = settings.Get("CrashReports", "AllowCrashReports")
if ALLOW_CRASH_REPORTS == None:
    variables.PAGE = "CrashReport"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
NORMAL = "\033[0m"


def SendCrashReport(type:str, message:str, additional=None):
    if message.strip() == "":
        return
    CurrentTime = time.time()
    console.RestoreConsole()
    try:
        if ALLOW_CRASH_REPORTS == True and settings.Get("CrashReports", "LastCrashReport", 0) + 300 < CurrentTime:
            additional = {
                "version": variables.VERSION + " (ETS2LA-Lite)",
                "os": variables.OS,
                "language": "en",
                "custom": additional
            }

            jsonData = {
                "type": type,
                "message": message,
                "additional": additional
            }

            url = 'https://crash.tumppi066.fi/crash'
            headers = {'Content-Type': 'application/json'}
            data = json.dumps(jsonData)
            try:
                response = requests.post(url, headers=headers, data=data)
                if response.status_code == 200:
                    print(GREEN + "\nCrash report sent successfully!" + NORMAL)
                else:
                    print(RED + f"\nFailed to send crash report (Server responded with {response.status_code})." + NORMAL)
            except:
                print(RED + f"\nUnexpected error occurred while sending the crash report:{NORMAL}\n{str(str(traceback.format_exc()))}")
        elif ALLOW_CRASH_REPORTS == False:
            print(YELLOW + "\nCrash detected, but crash reports are disabled in the settings. No report was sent." + NORMAL)
        else:
            print(YELLOW + "\nCrash detected, but the crash report rate limit has been reached. No report was sent." + NORMAL)
    except:
        print(RED + f"\nCrash report sending failed due to an unexpected error:{NORMAL}\n{str(traceback.format_exc())}")
    while message.endswith('\n'):
        message = message[:-1]
    message = f"{RED}>{NORMAL} " + message.replace("\n", f"\n{RED}>{NORMAL} ")
    print(f"{RED}{type}{NORMAL}\n{message}\n")
    ProcessName = multiprocessing.current_process().name
    if ProcessName != "MainProcess":
        variables.QUEUE.put({"POPUP": [f"{ProcessName} Crashed!", 0, 0.5]})
        variables.QUEUE.put({"MANAGEPLUGINS": [str(ProcessName), "Stop"]})
        while True: time.sleep(1)


def GetUserCount():
    if ALLOW_CRASH_REPORTS == False:
        variables.USERCOUNT = "Please enable crash reporting to fetch user count."
        return "Please enable crash reporting to fetch user count."

    try:
        url = 'https://crash.tumppi066.fi/usercount'
        response = json.loads(requests.get(url, timeout=1).text)
        variables.USERCOUNT = response["usercount"]
        return response["usercount"]
    except:
        variables.USERCOUNT = "Could not get user count."
        return "Could not get user count."


def Ping():
    try:
        LastPing = settings.Get("CrashReports", "LastPing", 0)
        CurrentTime = time.time()
        if LastPing + 59 < CurrentTime:
            settings.Set("CrashReports", "LastPing", CurrentTime)
            requests.get("https://crash.tumppi066.fi/ping", timeout=1)
    except:
        pass