import src.uicomponents as uicomponents
import src.translate as translate
import src.variables as variables
import src.settings as settings
import src.console as console
import src.updater as updater
import src.server as server

import numpy as np
import subprocess
import webbrowser
import threading
import ctypes
import mouse
import math
import time
import cv2

if variables.OS == "nt":
    from ctypes import windll, byref, sizeof, c_int
    import win32gui, win32con

def Initialize():
    width = settings.Get("UI", "Width", 700)
    height = settings.Get("UI", "Height", 400)
    x = settings.Get("UI", "X", 0)
    y = settings.Get("UI", "Y", 0)

    if width < 50 or height < 50:
        width = 700
        height = 400

    variables.BACKGROUND = np.zeros((height, width, 3), np.uint8)
    variables.BACKGROUND[:] = variables.BACKGROUND_COLOR
    if variables.TITLE_BAR_HEIGHT > 0:
        cv2.rectangle(variables.BACKGROUND, (0, 0), (width - 1, variables.TITLE_BAR_HEIGHT - 1), variables.TAB_BAR_COLOR, -1)

    variables.CONTEXT_MENU_ITEMS = [
        {"name": "Restart",
        "function": lambda: {Restart(), setattr(variables, "CONTEXT_MENU", [False, 0, 0]), setattr(variables, "RENDER_FRAME", True)}},
        {"name": "Close",
        "function": lambda: {Close(), setattr(variables, "CONTEXT_MENU", [False, 0, 0]), setattr(variables, "RENDER_FRAME", True)}},
        {"name": "Search for updates",
        "function": lambda: {updater.CheckForUpdates(False), setattr(variables, "CONTEXT_MENU", [False, 0, 0]), setattr(variables, "RENDER_FRAME", True)}}]

    cv2.namedWindow(variables.NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(variables.NAME, width, height)
    cv2.imshow(variables.NAME, variables.BACKGROUND)
    cv2.waitKey(1)

    if variables.OS == "nt":
        variables.HWND = win32gui.FindWindow(None, variables.NAME)
        if variables.TITLE_BAR_HEIGHT == 0:
            windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int((variables.BACKGROUND_COLOR[0] << 16) | (variables.BACKGROUND_COLOR[1] << 8) | variables.BACKGROUND_COLOR[2])), sizeof(c_int))
        else:
            windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int((variables.TAB_BAR_COLOR[0] << 16) | (variables.TAB_BAR_COLOR[1] << 8) | variables.TAB_BAR_COLOR[2])), sizeof(c_int))
        hicon = win32gui.LoadImage(None, f"{variables.PATH}app/assets/favicon.ico", win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE)
        win32gui.SendMessage(variables.HWND, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
        win32gui.SendMessage(variables.HWND, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

    Update()

def Resize(width, height):
    variables.BACKGROUND = np.zeros((height, width, 3), np.uint8)
    variables.BACKGROUND[:] = variables.BACKGROUND_COLOR
    if variables.TITLE_BAR_HEIGHT > 0:
        cv2.rectangle(variables.BACKGROUND, (0, 0), (width - 1, variables.TITLE_BAR_HEIGHT - 1), variables.TAB_BAR_COLOR, -1)
    variables.CANVAS_BOTTOM = height - 1 - variables.TITLE_BAR_HEIGHT
    variables.CANVAS_RIGHT = width - 1
    variables.RENDER_FRAME = True

def Restart():
    if variables.DEVMODE == True:
        subprocess.Popen(f"python {variables.PATH}app/main.py --dev", cwd=variables.PATH)
    else:
        subprocess.Popen(f"{variables.PATH}Start.bat", cwd=variables.PATH, creationflags=subprocess.CREATE_NEW_CONSOLE)
    Close()

def Close():
    translate.SaveCache()
    settings.Set("UI", "X", variables.X)
    settings.Set("UI", "Y", variables.Y)
    settings.Set("UI", "Width", variables.WIDTH)
    settings.Set("UI", "Height", variables.HEIGHT)
    console.RestoreConsole()
    console.CloseConsole()
    variables.BREAK = True

def SetTitleBarHeight(title_bar_height):
    if variables.OS == "nt":
        if int(win32gui.IsIconic(variables.HWND)) == 1:
            cv2.imshow(variables.NAME, variables.CACHED_FRAME)
            cv2.waitKey(1)
            return
    try:
        x, y, width, height = cv2.getWindowImageRect(variables.NAME)
    except:
        Close()
        return
    variables.TITLE_BAR_HEIGHT = title_bar_height
    variables.BACKGROUND = np.zeros((height, width, 3), np.uint8)
    variables.BACKGROUND[:] = variables.BACKGROUND_COLOR
    if title_bar_height > 0:
        cv2.rectangle(variables.BACKGROUND, (0, 0), (width - 1, variables.TITLE_BAR_HEIGHT - 1), variables.TAB_BAR_COLOR, -1)
    if variables.OS == "nt":
        if title_bar_height == 0:
            from ctypes import windll, byref, sizeof, c_int
            windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int((variables.BACKGROUND_COLOR[0] << 16) | (variables.BACKGROUND_COLOR[1] << 8) | variables.BACKGROUND_COLOR[2])), sizeof(c_int))
        else:
            from ctypes import windll, byref, sizeof, c_int
            windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int((variables.TAB_BAR_COLOR[0] << 16) | (variables.TAB_BAR_COLOR[1] << 8) | variables.TAB_BAR_COLOR[2])), sizeof(c_int))
    variables.CANVAS_BOTTOM = height - 1 - variables.TITLE_BAR_HEIGHT
    variables.CANVAS_RIGHT = width - 1
    variables.RENDER_FRAME = True

def Update():
    current_time = time.time()

    if variables.OS == "nt":
        if int(win32gui.IsIconic(variables.HWND)) == 1:
            cv2.imshow(variables.NAME, variables.CACHED_FRAME)
            cv2.waitKey(1)
            return

    try:
        x, y, width, height = cv2.getWindowImageRect(variables.NAME)
        if (x, y, width, height) != (variables.X, variables.Y, variables.WIDTH, variables.HEIGHT):
            variables.X, variables.Y, variables.WIDTH, variables.HEIGHT = x, y, width, height
            Resize(width, height)
        mouse_x, mouse_y = mouse.get_position()
        mouse_relative_window = mouse_x - x, mouse_y - y
        if width != 0 and height != 0:
            mouse_x = mouse_relative_window[0]/width
            mouse_y = mouse_relative_window[1]/height
        else:
            mouse_x = 0
            mouse_y = 0
        last_left_clicked = uicomponents.left_clicked
        last_right_clicked = uicomponents.right_clicked
        foreground_window = ctypes.windll.user32.GetForegroundWindow() == ctypes.windll.user32.FindWindowW(None, variables.NAME)
        left_clicked = ctypes.windll.user32.GetKeyState(0x01) & 0x8000 != 0 and foreground_window
        right_clicked = ctypes.windll.user32.GetKeyState(0x02) & 0x8000 != 0 and foreground_window
        uicomponents.foreground_window = foreground_window
        uicomponents.frame_width = width
        uicomponents.frame_height = height
        uicomponents.mouse_x = mouse_x
        uicomponents.mouse_y = mouse_y
        uicomponents.last_left_clicked = uicomponents.left_clicked
        uicomponents.last_right_clicked = uicomponents.right_clicked
        uicomponents.left_clicked = left_clicked
        uicomponents.right_clicked = right_clicked
    except:
        Close()
        return

    if variables.TITLE_BAR_HEIGHT > 0:
        for i, tab in enumerate(variables.TABS):
            variables.ITEMS.append({
                "type": "button",
                "text": tab,
                "function": lambda tab = tab: {setattr(variables, "PAGE", tab), settings.Set("UI", "Page", tab)},
                "x1": i / len(variables.TABS) * variables.CANVAS_RIGHT + 5,
                "y1": -variables.TITLE_BAR_HEIGHT + 6,
                "x2": (i + 1) / len(variables.TABS) * variables.CANVAS_RIGHT - 5,
                "y2": -6,
                "button_selected": variables.PAGE == tab,
                "button_color": variables.TAB_BUTTON_COLOR,
                "button_hover_color": variables.TAB_BUTTON_HOVER_COLOR,
                "button_selected_color": variables.TAB_BUTTON_SELECTED_COLOR,
                "button_selected_hover_color": variables.TAB_BUTTON_SELECTED_HOVER_COLOR})

    if variables.PAGE == "Update":
        variables.ITEMS.append({
            "type": "label",
            "text": f"Update Available:\n{variables.VERSION} -> {variables.REMOTE_VERSION}",
            "x1": 0,
            "y1": 10,
            "x2": variables.CANVAS_RIGHT,
            "y2": 50})

        variables.ITEMS.append({
            "type": "label",
            "text": f"Changelog:\n\n{variables.CHANGELOG}\n\n",
            "x1": 0,
            "y1": 60,
            "x2": variables.CANVAS_RIGHT,
            "y2": variables.CANVAS_BOTTOM - 90})

        variables.ITEMS.append({
            "type": "button",
            "text": "Update",
            "function": lambda: updater.Update(),
            "x1": variables.CANVAS_RIGHT / 2 + 10,
            "y1": variables.CANVAS_BOTTOM - 70,
            "x2": variables.CANVAS_RIGHT - 20,
            "y2": variables.CANVAS_BOTTOM - 20})

        variables.ITEMS.append({
            "type": "button",
            "text": "Don't Update",
            "function": lambda: {SetTitleBarHeight(50), setattr(variables, "PAGE", "Menu")},
            "x1": 20,
            "y1": variables.CANVAS_BOTTOM - 70,
            "x2": variables.CANVAS_RIGHT / 2 - 10,
            "y2": variables.CANVAS_BOTTOM - 20})

    if variables.PAGE == "CrashReport":
        variables.ITEMS.append({
            "type": "label",
            "text": "CrashReporter",
            "x1": 0,
            "y1": 10,
            "x2": variables.CANVAS_RIGHT,
            "y2": 50})

        variables.ITEMS.append({
            "type": "label",
            "text": "Do you want the app to send anonymous crash reports to the developers?\nNo personal information is sent and all paths have the username censored.\nWe take all crash reports seriously and will try to fix the issue as soon as possible.\nDo you want to enable the crash reporting?",
            "x1": 0,
            "y1": 60,
            "x2": variables.CANVAS_RIGHT,
            "y2": variables.CANVAS_BOTTOM - 90})

        variables.ITEMS.append({
            "type": "button",
            "text": "Yes",
            "function": lambda: {SetTitleBarHeight(50), setattr(variables, "PAGE", "Menu"), setattr(server, "ALLOW_CRASH_REPORTS", True), settings.Get("CrashReports", "AllowCrashReports", True)},
            "x1": variables.CANVAS_RIGHT / 2 + 10,
            "y1": variables.CANVAS_BOTTOM - 70,
            "x2": variables.CANVAS_RIGHT - 20,
            "y2": variables.CANVAS_BOTTOM - 20})

        variables.ITEMS.append({
            "type": "button",
            "text": "No",
            "function": lambda: {SetTitleBarHeight(50), setattr(variables, "PAGE", "Menu"), setattr(server, "ALLOW_CRASH_REPORTS", False), settings.Get("CrashReports", "AllowCrashReports", False)},
            "x1": 20,
            "y1": variables.CANVAS_BOTTOM - 70,
            "x2": variables.CANVAS_RIGHT / 2 - 10,
            "y2": variables.CANVAS_BOTTOM - 20})

    if variables.PAGE == "Menu":
        variables.ITEMS.append({
            "type": "label",
            "text": f"ETS2LA-Lite v{variables.VERSION}",
            "fontsize": variables.FONT_SIZE * 1.3,
            "x1": 0,
            "y1": 5,
            "x2": variables.CANVAS_RIGHT,
            "y2": variables.TITLE_BAR_HEIGHT - 5})

        variables.ITEMS.append({
            "type": "label",
            "text": f"Users online: {variables.USERCOUNT}",
            "text_color": (128, 128, 128),
            "x1": 0,
            "y1": variables.CANVAS_BOTTOM - variables.TITLE_BAR_HEIGHT + 5,
            "x2": variables.CANVAS_RIGHT,
            "y2": variables.CANVAS_BOTTOM - 5})

        variables.ITEMS.append({
            "type": "button",
            "text": "Open ETS2LA Website",
            "function": lambda: webbrowser.open("https://ets2la.com"),
            "x1": variables.CANVAS_RIGHT * 0.25,
            "y1": variables.CANVAS_BOTTOM / 2 - variables.TITLE_BAR_HEIGHT * 1.5 + 5,
            "x2": variables.CANVAS_RIGHT * 0.75,
            "y2": variables.CANVAS_BOTTOM / 2 - variables.TITLE_BAR_HEIGHT / 2 - 5})

        variables.ITEMS.append({
            "type": "button",
            "text": "Open GitHub Website",
            "function": lambda: webbrowser.open("https://github.com/ETS2LA"),
            "x1": variables.CANVAS_RIGHT * 0.25,
            "y1": variables.CANVAS_BOTTOM / 2 - variables.TITLE_BAR_HEIGHT / 2 + 5,
            "x2": variables.CANVAS_RIGHT * 0.75,
            "y2": variables.CANVAS_BOTTOM / 2 + variables.TITLE_BAR_HEIGHT / 2 - 5})

        variables.ITEMS.append({
            "type": "button",
            "text": "Open ETS2LA Discord",
            "function": lambda: webbrowser.open("https://discord.gg/ETS2LA"),
            "x1": variables.CANVAS_RIGHT * 0.25,
            "y1": variables.CANVAS_BOTTOM / 2 + variables.TITLE_BAR_HEIGHT / 2 + 5,
            "x2": variables.CANVAS_RIGHT * 0.75,
            "y2": variables.CANVAS_BOTTOM / 2 + variables.TITLE_BAR_HEIGHT * 1.5 - 5})

    if variables.PAGE == "Settings":
        variables.ITEMS.append({
            "type": "switch",
            "text": "Hide Console",
            "setting": ("Console", "HideConsole", False),
            "function": lambda: {console.HideConsole() if settings.Get("Console", "HideConsole", False) else console.RestoreConsole()},
            "x1": 10,
            "y1": 11,
            "x2": variables.CANVAS_RIGHT - 10,
            "y2": 31})

        variables.ITEMS.append({
            "type": "switch",
            "text": "Send Anonymous Crash Reports",
            "setting": ("CrashReports", "AllowCrashReports", None),
            "function": lambda: {setattr(server, "ALLOW_CRASH_REPORTS", settings.Get("CrashReports", "AllowCrashReports")), threading.Thread(target=server.GetUserCount, daemon=True).start()},
            "x1": 10,
            "y1": 41,
            "x2": variables.CANVAS_RIGHT - 10,
            "y2": 61})

        variables.ITEMS.append({
            "type": "dropdown",
            "text": "Language",
            "items": [name for name, _ in translate.GetAvailableLanguages().items()],
            "default_item": 27,
            "function": lambda: {
                translate.SaveCache(),
                settings.Set("UI", "Language", translate.GetAvailableLanguages()[[name for name, _ in translate.GetAvailableLanguages().items()][variables.DROPDOWNS["Language"][1]]]),
                setattr(variables, "LANGUAGE", settings.Get("UI", "Language", "en")),
                setattr(variables, "TRANSLATION_CACHE", {}),
                setattr(variables, "RENDER_FRAME", True),
                translate.Initialize()
                },
            "x1": 10,
            "y1": 71,
            "x2": variables.CANVAS_RIGHT / 2 - 5,
            "y2": 106})

        variables.ITEMS.append({
            "type": "dropdown",
            "text": "Theme",
            "items": ["Dark", "Light"],
            "default_item": 0,
            "function": lambda: {
                settings.Set("UI", "Theme", ["dark", "light"][variables.DROPDOWNS["Theme"][1]]),
                Restart() if variables.THEME != settings.Get("UI", "Theme", "dark") else None
                },
            "x1": variables.CANVAS_RIGHT / 2 + 5,
            "y1": 71,
            "x2": variables.CANVAS_RIGHT - 10,
            "y2": 106})

    if variables.CONTEXT_MENU[0]:
        offset = 0
        for item in variables.CONTEXT_MENU_ITEMS:
            variables.ITEMS.append({
                "type": "button",
                "text": item["name"],
                "function": item["function"],
                "x1": variables.CONTEXT_MENU[1] * variables.CANVAS_RIGHT,
                "y1": variables.CONTEXT_MENU[2] * (variables.CANVAS_BOTTOM + variables.TITLE_BAR_HEIGHT) - variables.TITLE_BAR_HEIGHT + offset,
                "x2": variables.CONTEXT_MENU[1] * variables.CANVAS_RIGHT + 200,
                "y2": variables.CONTEXT_MENU[2] * (variables.CANVAS_BOTTOM + variables.TITLE_BAR_HEIGHT) - variables.TITLE_BAR_HEIGHT + offset + 30})
            offset += 35

    if variables.LAST_POPUP[0] != variables.POPUP:
        if variables.LAST_POPUP[0][0] == None:
            variables.LAST_POPUP = variables.POPUP, current_time
            variables.POPUP_SHOW_VALUE = 1
        else:
            variables.LAST_POPUP = variables.POPUP, current_time - 1
            variables.POPUP_SHOW_VALUE = 0
        variables.RENDER_FRAME = True
    elif variables.POPUP[0] != None and variables.LAST_POPUP[1] + 5 < current_time:
        variables.POPUP = [None, 0, 0.5]
        variables.LAST_POPUP = [None, 0, 0.5], 0
        variables.POPUP_SHOW_VALUE = 1
        variables.RENDER_FRAME = True
    elif variables.POPUP[0] != None and variables.LAST_POPUP[1] + 4.5 < current_time:
        variables.POPUP_SHOW_VALUE = -(math.cos(math.pi * ((current_time - variables.LAST_POPUP[1] - 4.5) * 2)) - 1) / 2
        variables.RENDER_FRAME = True
    elif variables.LAST_POPUP[1] + 0.5 > current_time:
        variables.POPUP_SHOW_VALUE = math.pow(2, 10 * (1 - (current_time - variables.LAST_POPUP[1]) * 2) - 10)
        variables.RENDER_FRAME = True

    for area in variables.AREAS:
        if area[0] != "label":
            if (area[1] <= mouse_x * width <= area[3] and area[2] <= mouse_y * height <= area[4]) != area[5]:
                area = (area[1], area[2], area[3], area[4], not area[5])
                variables.RENDER_FRAME = True

    if foreground_window == False and variables.CACHED_FRAME is not None and variables.POPUP[0] == None:
        variables.RENDER_FRAME = False

    if variables.RENDER_FRAME or last_left_clicked != left_clicked:
        variables.RENDER_FRAME = False
        #print(f"Rendering new frame!")

        variables.FRAME = variables.BACKGROUND.copy()
        variables.AREAS = []

        for item in variables.ITEMS:
            item_type = item["type"]
            item.pop("type")
            item_function = None
            if "function" in item:
                item_function = item["function"]
                item.pop("function")

            if item_type == "label":
                uicomponents.Label(**item)

            elif item_type == "button":
                changed, pressed, hovered = uicomponents.Button(**item)
                variables.AREAS.append((item_type, item["x1"], item["y1"] + variables.TITLE_BAR_HEIGHT, item["x2"], item["y2"] + variables.TITLE_BAR_HEIGHT, pressed or hovered))

                if changed and (variables.CONTEXT_MENU[0] == False or item["text"] in str(variables.CONTEXT_MENU_ITEMS)):
                    if item_function is not None:
                        item_function()
                    else:
                        variables.RENDER_FRAME = True

            elif item_type == "switch":
                changed, pressed, hovered = uicomponents.Switch(**item)
                variables.AREAS.append((item_type, item["x1"], item["y1"] + variables.TITLE_BAR_HEIGHT, item["x2"], item["y2"] + variables.TITLE_BAR_HEIGHT, pressed or hovered))

                if changed:
                    if item_function is not None:
                        item_function()

            elif item_type == "dropdown":
                changed, pressed, hovered = uicomponents.Dropdown(**item)
                variables.AREAS.append((item_type, item["x1"], item["y1"] + variables.TITLE_BAR_HEIGHT, item["x2"], item["y2"] + variables.TITLE_BAR_HEIGHT, pressed or hovered))

                if changed:
                    if item_function is not None:
                        item_function()

        if len(variables.ITEMS) < len(variables.TABS) + 1 and variables.TITLE_BAR_HEIGHT != 0:
            uicomponents.Label(
                text="\n\nYou landed on an empty page...\nPlease report how you got here!\n\n",
                x1=0,
                y1=0,
                x2=variables.CANVAS_RIGHT - 1,
                y2=variables.CANVAS_BOTTOM)

        if variables.POPUP[0] != None:
            if variables.POPUP_SHOW_VALUE < 0.01:
                variables.POPUP_SHOW_VALUE = 0
            elif variables.POPUP_SHOW_VALUE > 0.99:
                variables.POPUP_SHOW_VALUE = 1
            x1 = variables.CANVAS_RIGHT * (0.5 - variables.POPUP[2] / 2)
            y1 = variables.CANVAS_BOTTOM - variables.POPUP_HEIGHT + variables.POPUP_HEIGHT * variables.POPUP_SHOW_VALUE
            x2 = variables.CANVAS_RIGHT * (0.5 + variables.POPUP[2] / 2)
            y2 = variables.CANVAS_BOTTOM - variables.POPUP_HEIGHT * 0.25 + variables.POPUP_HEIGHT * variables.POPUP_SHOW_VALUE
            uicomponents.Button(
                text=str(variables.POPUP[0]),
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                button_color=variables.POPUP_COLOR,
                button_hover_color=variables.POPUP_HOVER_COLOR)
            if variables.POPUP[1] > 0:
                cv2.line(variables.FRAME,
                        (round(x1 + round(variables.POPUP_HEIGHT / 20) / 2), round(variables.POPUP_HEIGHT + y2 + variables.POPUP_HEIGHT / 40)),
                        (round(x1 - round(variables.POPUP_HEIGHT / 20) / 2 + variables.CANVAS_RIGHT * variables.POPUP[2] * (variables.POPUP[1] / 100)), round(variables.POPUP_HEIGHT + y2 + variables.POPUP_HEIGHT / 40)),
                        variables.POPUP_PROGRESS_COLOR, round(variables.POPUP_HEIGHT / 20))

        variables.CACHED_FRAME = variables.FRAME.copy()

        if last_left_clicked == True and left_clicked == False:
            variables.CONTEXT_MENU = [False, mouse_x, mouse_y]
            variables.RENDER_FRAME = True

    if last_right_clicked == True and right_clicked == False:
        variables.CONTEXT_MENU = [True, mouse_x, mouse_y]
        variables.RENDER_FRAME = True

    variables.ITEMS = []

    cv2.imshow(variables.NAME, variables.CACHED_FRAME)
    cv2.waitKey(1)