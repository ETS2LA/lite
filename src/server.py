import src.variables as variables
import src.settings as settings
import requests
import json
import time

ALLOW_CRASH_REPORTS = settings.Get("CrashReports", "AllowCrashReports")
if ALLOW_CRASH_REPORTS == None:
    if input("Do you want to allow crash reports to be sent to the developers? This will help us fix bugs faster.\n\nCrash reports are anonymous and will not contain any personal information").lower() == "yes":
        ALLOW_CRASH_REPORTS = True
        settings.Create("CrashReports", "AllowCrashReports", True)
    else:
        settings.Create("CrashReports", "AllowCrashReports", False)
        ALLOW_CRASH_REPORTS = False

def SendCrashReport(type:str, message:str, additional=None):
    """Will send a crash report to the main application server. This will then be forwarded to the developers on discord.

    Args:
        type (str): Crash type
        message (str): Crash message
        additional (_type_, optional): Additional text / information. Defaults to None.

    Returns:
        success (bool): False if not successful, True if successful
    """

    if message.strip() == "":
        return False

    try:
        if ALLOW_CRASH_REPORTS:
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
    """Get the amount of users using the app. This will be shown to the user when the app is opened.

    Returns:
        str: User count
    """

    if not ALLOW_CRASH_REPORTS:
        return "Please enable crash reporting to fetch user count."

    try:
        url = 'https://crash.tumppi066.fi/usercount'
        response = json.loads(requests.get(url, timeout=1).text)
        return response["usercount"]
    except:
        return "Could not get user count."

def Ping():
    """Will send a ping to the server, doesn't send any data."""
    try:
        last_ping = float(settings.Get("CrashReports", "last_ping", 0))
        current_time = time.time()
        if last_ping + 59 < current_time:
            url = 'https://crash.tumppi066.fi/ping'
            requests.get(url, timeout=1)
            settings.Create("CrashReports", "last_ping", str(current_time))
    except:
        pass