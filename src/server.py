import src.variables as variables
import src.settings as settings
import requests
import json


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
        if settings.Get("CrashReports", "AllowCrashReports", False):

            additional = {
                "version": variables.VERSION,
                "os": variables.OS,
                "language": settings.GetSettings("User Interface", "DestinationLanguage"),
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