import plugins.NavigationDetectionAI.main as NavigationDetectionAI
import src.uicomponents as uicomponents
import src.variables as variables
import src.settings as settings
import src.console as console
import src.updater as updater
import src.setup as setup

import numpy as np
import subprocess
import ctypes
import mouse
import cv2

def Initialize():
    width = settings.Get("UI", "Width", 700)
    height = settings.Get("UI", "Height", 400)
    x = settings.Get("UI", "X", 0)
    y = settings.Get("UI", "Y", 0)

    variables.BACKGROUND = np.zeros((height, width, 3), np.uint8)
    variables.BACKGROUND[:] = (28 if variables.THEME == "dark" else 250)
    cv2.rectangle(variables.BACKGROUND, (0, 0), (width - 1, variables.TITLE_BAR_HEIGHT - 1), (47, 47, 47) if variables.THEME == "dark" else (231, 231, 231), -1)

    if variables.OS == "nt":
        from ctypes import windll, byref, sizeof, c_int
        import win32gui, win32con

    cv2.namedWindow(variables.NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(variables.NAME, width, height)
    cv2.imshow(variables.NAME, variables.BACKGROUND)
    cv2.waitKey(1)

    if variables.OS == "nt":
        variables.HWND = win32gui.FindWindow(None, variables.NAME)
        windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int((0x2F2F2F) if variables.THEME == "dark" else (0xE7E7E7))), sizeof(c_int))
        hicon = win32gui.LoadImage(None, f"{variables.PATH}assets/favicon.ico", win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE)
        win32gui.SendMessage(variables.HWND, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
        win32gui.SendMessage(variables.HWND, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

def Resize(width, height):
    variables.BACKGROUND = np.zeros((height, width, 3), np.uint8)
    variables.BACKGROUND[:] = (28 if variables.THEME == "dark" else 250)
    if variables.TITLE_BAR_HEIGHT > 0:
        cv2.rectangle(variables.BACKGROUND, (0, 0), (width - 1, variables.TITLE_BAR_HEIGHT - 1), (47, 47, 47) if variables.THEME == "dark" else (231, 231, 231), -1)
    variables.CANVAS_BOTTOM = height - 1 - variables.TITLE_BAR_HEIGHT
    variables.CANVAS_RIGHT = width - 1
    variables.RENDER_FRAME = True

def Restart():
    subprocess.Popen(f"Start.bat", cwd=variables.PATH, creationflags=subprocess.CREATE_NEW_CONSOLE)
    Close()

def Close():
    settings.Set("UI", "X", variables.X)
    settings.Set("UI", "Y", variables.Y)
    settings.Set("UI", "Width", variables.WIDTH)
    settings.Set("UI", "Height", variables.HEIGHT)
    console.RestoreConsole()
    console.CloseConsole()
    variables.BREAK = True

def SetTitleBarHeight(title_bar_height):
    try:
        x, y, width, height = cv2.getWindowImageRect(variables.NAME)
    except:
        Close()
        return
    variables.TITLE_BAR_HEIGHT = title_bar_height
    variables.BACKGROUND = np.zeros((height, width, 3), np.uint8)
    variables.BACKGROUND[:] = (28 if variables.THEME == "dark" else 250)
    if title_bar_height > 0:
        cv2.rectangle(variables.BACKGROUND, (0, 0), (width - 1, variables.TITLE_BAR_HEIGHT - 1), (47, 47, 47) if variables.THEME == "dark" else (231, 231, 231), -1)
    if variables.OS == "nt":
        if title_bar_height == 0:
            from ctypes import windll, byref, sizeof, c_int
            windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int((0x1C1C1C) if variables.THEME == "dark" else (0xFAFAFA))), sizeof(c_int))
        else:
            from ctypes import windll, byref, sizeof, c_int
            windll.dwmapi.DwmSetWindowAttribute(variables.HWND, 35, byref(c_int((0x2F2F2F) if variables.THEME == "dark" else (0xE7E7E7))), sizeof(c_int))
    variables.CANVAS_BOTTOM = height - 1 - variables.TITLE_BAR_HEIGHT
    variables.CANVAS_RIGHT = width - 1
    variables.RENDER_FRAME = True

def Update():
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
                "function": None,
                "x1": i / len(variables.TABS) * variables.CANVAS_RIGHT + 5,
                "y1": -variables.TITLE_BAR_HEIGHT + 6,
                "x2": (i + 1) / len(variables.TABS) * variables.CANVAS_RIGHT - 5,
                "y2": -6,
                "button_selected": variables.TAB == tab,
                "button_color": (47, 47, 47) if variables.THEME == "dark" else (231, 231, 231),
                "button_hover_color": (41, 41, 41) if variables.THEME == "dark" else (244, 244, 244),
                "button_selected_color": (28, 28, 28) if variables.THEME == "dark" else (250, 250, 250),
                "button_selected_hover_color": (28, 28, 28) if variables.THEME == "dark" else (250, 250, 250)})

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

    if last_right_clicked == True and right_clicked == False:
        variables.CONTEXT_MENU = [True, mouse_x, mouse_y]

    if variables.CONTEXT_MENU:
        if variables.CONTEXT_MENU[0]:
            variables.ITEMS.append({
                "type": "button",
                "text": "Restart",
                "function": lambda: Restart(),
                "x1": variables.CONTEXT_MENU[1] * variables.CANVAS_RIGHT,
                "y1": variables.CONTEXT_MENU[2] * (variables.CANVAS_BOTTOM + variables.TITLE_BAR_HEIGHT) - variables.TITLE_BAR_HEIGHT,
                "x2": variables.CONTEXT_MENU[1] * variables.CANVAS_RIGHT + 200,
                "y2": variables.CONTEXT_MENU[2] * (variables.CANVAS_BOTTOM + variables.TITLE_BAR_HEIGHT) - variables.TITLE_BAR_HEIGHT + 30})
            variables.ITEMS.append({
                "type": "button",
                "text": "Close",
                "function": lambda: Close(),
                "x1": variables.CONTEXT_MENU[1] * variables.CANVAS_RIGHT,
                "y1": variables.CONTEXT_MENU[2] * (variables.CANVAS_BOTTOM + variables.TITLE_BAR_HEIGHT) - variables.TITLE_BAR_HEIGHT + 35,
                "x2": variables.CONTEXT_MENU[1] * variables.CANVAS_RIGHT + 200,
                "y2": variables.CONTEXT_MENU[2] * (variables.CANVAS_BOTTOM + variables.TITLE_BAR_HEIGHT) - variables.TITLE_BAR_HEIGHT + 65})
            variables.ITEMS.append({
                "type": "button",
                "text": "Search for updates",
                "function": lambda: updater.CheckForUpdates(),
                "x1": variables.CONTEXT_MENU[1] * variables.CANVAS_RIGHT,
                "y1": variables.CONTEXT_MENU[2] * (variables.CANVAS_BOTTOM + variables.TITLE_BAR_HEIGHT) - variables.TITLE_BAR_HEIGHT + 70,
                "x2": variables.CONTEXT_MENU[1] * variables.CANVAS_RIGHT + 200,
                "y2": variables.CONTEXT_MENU[2] * (variables.CANVAS_BOTTOM + variables.TITLE_BAR_HEIGHT) - variables.TITLE_BAR_HEIGHT + 100})

    if variables.PAGE == "Menu":
        ...

    for area in variables.AREAS:
        if area[0] == "button" or area[0] == "buttonlist":
            if (area[1] <= mouse_x * width <= area[3] and area[2] <= mouse_y * height <= area[4]) != area[5]:
                area = (area[1], area[2], area[3], area[4], not area[5])
                variables.RENDER_FRAME = True

    if foreground_window == False and variables.CACHED_FRAME is not None:
        variables.RENDER_FRAME = False

    if variables.RENDER_FRAME or last_left_clicked != left_clicked or last_right_clicked != right_clicked:
        variables.RENDER_FRAME = False
        print("Rendering new frame!")

        variables.FRAME = variables.BACKGROUND.copy()
        variables.AREAS = []

        for item in variables.ITEMS:
            item_type = item["type"]
            item.pop("type")
            if item_type == "button":
                item_function = item["function"]
                item.pop("function")

            if item_type == "label":
                uicomponents.Label(**item)

            if item_type == "button":
                pressed, hovered = uicomponents.Button(**item)
                variables.AREAS.append((item_type, item["x1"], item["y1"] + variables.TITLE_BAR_HEIGHT, item["x2"], item["y2"] + variables.TITLE_BAR_HEIGHT, pressed or hovered))

                if pressed:
                    if item_function is not None:
                        item_function()
                    else:
                        variables.RENDER_FRAME = True
                        for tab in variables.TABS:
                            if item["text"] == tab:
                                variables.TAB = tab

        if len(variables.ITEMS) < len(variables.TABS) + 1 and variables.TITLE_BAR_HEIGHT != 0:
            uicomponents.Label(
                text="\n\nYou landed on an empty page...\nPlease report how you got here!\n\n",
                x1=0,
                y1=0,
                x2=variables.CANVAS_RIGHT - 1,
                y2=variables.CANVAS_BOTTOM)

        variables.CACHED_FRAME = variables.FRAME.copy()

    if last_left_clicked == True and left_clicked == False:
        variables.CONTEXT_MENU = [False, 0, 0]

    variables.ITEMS = []

    cv2.imshow(variables.NAME, variables.CACHED_FRAME)
    cv2.waitKey(1)