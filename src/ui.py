import plugins.NavigationDetectionAI.main as NavigationDetectionAI
import src.uicomponents as uicomponents
import src.variables as variables
import src.settings as settings
from src.classes import Button, Label
import src.console as console
import src.setup as setup
from typing import cast

import numpy as np
import ctypes
import mouse
import cv2

def InitializeUI():
    width = settings.Get("UI", "Width", 700)
    height = settings.Get("UI", "Height", 400)
    x = settings.Get("UI", "X", 0)
    y = settings.Get("UI", "Y", 0)
    variables.THEME = settings.Get("UI", "Theme", "dark")
    resizable = settings.Get("UI", "Resizable", False)

    # dark 1: 28, 28, 28
    # dark 2: 47, 47, 47
    # light 1: 250, 250, 250
    # light 2: 231, 231, 231
    variables.BACKGROUND = np.zeros((height, width, 3), np.uint8)
    variables.BACKGROUND[:] = (28 if variables.THEME == "dark" else 250)
    cv2.rectangle(variables.BACKGROUND, (0, 0), (width - 1, 49), (47, 47, 47) if variables.THEME == "dark" else (231, 231, 231), -1)

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

def CloseUI():
    settings.Create("UI", "X", variables.X)
    settings.Create("UI", "Y", variables.Y)
    settings.Create("UI", "Width", variables.WIDTH)
    settings.Create("UI", "Height", variables.HEIGHT)
    console.RestoreConsole()
    console.CloseConsole()
    try:
        cv2.destroyWindow(variables.NAME)
    except:
        pass
    variables.BREAK = True

def ResizeUI(width, height):
    variables.BACKGROUND = np.zeros((height, width, 3), np.uint8)
    variables.BACKGROUND[:] = (28 if variables.THEME == "dark" else 250)
    cv2.rectangle(variables.BACKGROUND, (0, 0), (width - 1, 49), (47, 47, 47) if variables.THEME == "dark" else (231, 231, 231), -1)
    variables.RENDER_FRAME = True

def HandleUI():
    try:
        x, y, width, height = cv2.getWindowImageRect(variables.NAME)
        if (x, y, width, height) != (variables.X, variables.Y, variables.WIDTH, variables.HEIGHT):
            variables.X, variables.Y, variables.WIDTH, variables.HEIGHT = x, y, width, height
            ResizeUI(width, height)
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
        left_clicked = ctypes.windll.user32.GetKeyState(0x01) & 0x8000 != 0 and ctypes.windll.user32.GetForegroundWindow() == ctypes.windll.user32.FindWindowW(None, variables.NAME)
        right_clicked = ctypes.windll.user32.GetKeyState(0x02) & 0x8000 != 0 and ctypes.windll.user32.GetForegroundWindow() == ctypes.windll.user32.FindWindowW(None, variables.NAME)
        uicomponents.frame_width = width
        uicomponents.frame_height = height
        uicomponents.mouse_x = mouse_x
        uicomponents.mouse_y = mouse_y
        uicomponents.last_left_clicked = uicomponents.left_clicked
        uicomponents.last_right_clicked = uicomponents.right_clicked
        uicomponents.left_clicked = left_clicked
        uicomponents.right_clicked = right_clicked
    except:
        CloseUI()
        return

    for i, tab in enumerate(variables.TABS):
        variables.ITEMS.append(Button(
            text=tab,
            x1=i / len(variables.TABS) * variables.WIDTH + 5,
            y1=0,
            x2=(i + 1) / len(variables.TABS) * variables.WIDTH - 5,
            y2=45,
            textColor=(255, 255, 255),
            fontSize=12,
            round_corners=10,
            buttonColor=(47, 47, 47) if variables.THEME == "dark" else (231, 231, 231),
            buttonHoverColor=(41, 41, 41) if variables.THEME == "dark" else (244, 244, 244),
            buttonSelectedColor=(28, 28, 28) if variables.THEME == "dark" else (250, 250, 250),
            buttonSelectedHoverColor=(28, 28, 28) if variables.THEME == "dark" else (250, 250, 250),
            buttonSelected = variables.TAB == tab
        ))

    if variables.PAGE == "Update":
        variables.ITEMS.append(Label(
            text="Update Available!",
            x1=0.5 * variables.WIDTH - 100,
            y1=60,
            x2=0.5 * variables.WIDTH + 100,
            y2=90,
            textColor=(255, 255, 255),
            fontSize=12
        ))

        variables.ITEMS.append(Button(
            text="Update",
            x1=0.75 * variables.WIDTH - 100,
            y1=120,
            x2=0.75 * variables.WIDTH + 100,
            y2=160,
            round_corners=10,
            buttonColor=(47, 47, 47),
            buttonHoverColor=(67, 67, 67),
            buttonSelectedColor=(67, 67, 67),
            textColor=(255, 255, 255),
            fontSize=12
        ))

        variables.ITEMS.append(Button(
            text="Don't Update",
            x1=0.25 * variables.WIDTH - 100,
            y1=120,
            x2=0.25 * variables.WIDTH + 100,
            y2=160,
            round_corners=10,
            buttonColor=(47, 47, 47),
            buttonHoverColor=(67, 67, 67),
            buttonSelectedColor=(67, 67, 67),
            textColor=(255, 255, 255),
            fontSize=12
        ))

    for area in variables.AREAS:
        if area[0] == Button:
            if (area[1] <= mouse_x * width <= area[3] and area[2] <= mouse_y * height <= area[4]) != area[5]:
                area = (area[1], area[2], area[3], area[4], not area[5])
                variables.RENDER_FRAME = True

    if variables.RENDER_FRAME or last_left_clicked != left_clicked:
        variables.RENDER_FRAME = False
        print("Rendering new frame!")
        
        variables.FRAME = variables.BACKGROUND.copy()
        variables.AREAS = []
        
        if len(variables.ITEMS) > 0:
            for item in variables.ITEMS:
                item_type = type(item)
                
                if item_type == Label:
                    item = cast(Label, item) # will give the item intellisense
                    uicomponents.DrawLabel(item)
                    
                if item_type == Button:
                    item = cast(Button, item) # will give the item intellisense
                    
                    pressed, hovered = uicomponents.DrawButton(item)
                    variables.AREAS.append((item_type, item.x1, item.y1, item.x2, item.y2, pressed or hovered))

                    if pressed:
                        variables.RENDER_FRAME = True
                        for tab in variables.TABS:
                            if item.text == tab:
                                variables.TAB = tab
        else:
            uicomponents.DrawLabel(Label(
                text="You landed on an empty page...",
                x1=0,
                y1=0,
                x2=variables.WIDTH,
                y2=variables.HEIGHT,
                textColor=(255, 255, 255),
                fontSize=12
            ))
        
        variables.CACHED_FRAME = variables.FRAME.copy()
    
    variables.ITEMS = []

    cv2.imshow(variables.NAME, variables.FRAME)
    cv2.waitKey(1)