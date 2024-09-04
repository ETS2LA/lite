import src.variables as variables
import src.settings as settings
import requests
import json
import time


ALLOW_CRASH_REPORTS = settings.Get("CrashReports", "AllowCrashReports")
if ALLOW_CRASH_REPORTS == None:
    variables.PAGE = "CrashReport"


def SendCrashReport(type:str, message:str, additional=None):
    if message.strip() == "":
        return False

    try:
        if ALLOW_CRASH_REPORTS == True:
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
            except:
                print("Could not connect to server to send crash report.")
            return response.status_code == 200
        else:
            print("Crash detected, but crash reports are not allowed to be sent.")
    except:
        import traceback
        traceback.print_exc()
        print("Crash report sending failed.")


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
        last_ping = float(settings.Get("CrashReports", "last_ping", 0))
        current_time = time.time()
        if last_ping + 59 < current_time:
            settings.Set("CrashReports", "last_ping", str(current_time))
            requests.get("https://crash.tumppi066.fi/ping", timeout=1)
    except:
        pass