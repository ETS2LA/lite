import numpy as np
import win32gui
import time
import cv2
import mss


SCT = mss.mss()
if len(SCT.monitors) < 2:
    print(f"ScreenCapture - Only one item in the monitor list, normally there should be at least two. ({str(SCT.monitors)})")
    monitor = SCT.monitors[0]
else:
    monitor = SCT.monitors[1]
screen_x = monitor["left"]
screen_y = monitor["top"]
screen_width = monitor["width"]
screen_height = monitor["height"]
last_window_positions = {}
last_foreground_windows = {}
last_track_window_updates = {}
last_track_window_route_advisor_updates = {}


# MARK: initialize()
def initialize(screen=None, area=(None, None, None, None)):
    """
    Initialize the ScreenCapture module. Needs to be called before the use of capture().

    Parameters
    ----------
    screen : int
        The index of the screen to capture. Defaults to primary screen. Format: 0 = primary screen
    area : tuple
        The area of the screen to capture in x1, y1, x2, y2. Defaults to entire screen.

    Returns
    -------
    None
    """
    global display
    global monitor
    global monitor_x1
    global monitor_y1
    global monitor_x2
    global monitor_y2
    global cam
    global capture_library
    global route_advisor_side
    global route_advisor_zoom_correct
    global route_advisor_tab_correct

    display = screen if screen != None else 0
    monitor = SCT.monitors[(display + 1)]
    monitor_x1 = area[0] if area[0] != None else monitor["left"]
    monitor_y1 = area[1] if area[1] != None else monitor["top"]
    monitor_x2 = area[2] if area[2] != None else monitor["width"]
    monitor_y2 = area[3] if area[3] != None else monitor["height"]
    cam = None
    capture_library = None
    route_advisor_side = "right"
    route_advisor_zoom_correct = True
    route_advisor_tab_correct = True

    try:

        try:

            from windows_capture import WindowsCapture, Frame, InternalCaptureControl
            capture = WindowsCapture(
                cursor_capture=False,
                draw_border=False,
                monitor_index=display + 1,
                window_name=None,
            )
            global windows_capture_frame
            global stop_windows_capture
            stop_windows_capture = False
            @capture.event
            def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
                global windows_capture_frame
                global stop_windows_capture
                windows_capture_frame = frame.convert_to_bgr().frame_buffer.copy()
                if stop_windows_capture:
                    stop_windows_capture = False
                    capture_control.stop()
            @capture.event
            def on_closed():
                print("capture Session Closed")
            try:
                control.stop()
            except:
                pass
            control = capture.start_free_threaded()

            capture_library = "WindowsCapture"

        except:

            import bettercam
            try:
                cam.stop()
            except:
                pass
            try:
                cam.close()
            except:
                pass
            try:
                cam.release()
            except:
                pass
            try:
                del cam
            except:
                pass
            cam = bettercam.create(output_idx=display, output_color="BGR")
            cam.start()
            cam.get_latest_frame()
            capture_library = "bettercam"

    except:

        capture_library = "mss"


# MARK: capture()
def capture(image_type:str = "both"):
    """
    Get the latest frame from the screen. Automatically chooses the capture library. Can't be used in a thread!

    Parameters
    ----------
    image_type : str
        The type of image to return. "both", "cropped", "full". Defaults to "both". "full" returns the entire screen, "cropped" returns the area of (x1, y1, x2, y2).

    Returns
    -------
    numpy.ndarray or numpy.ndarray, numpy.ndarray
        The return is based on the image_type.
    """

    if capture_library.lower() == "windowscapture":

        try:

            img = cv2.cvtColor(np.array(windows_capture_frame), cv2.COLOR_BGRA2BGR)
            if image_type.lower() == "both":
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img, img
            elif image_type.lower() == "cropped":
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img
            elif image_type.lower() == "full":
                return img
            else:
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img, img

        except:

            return None if image_type.lower() == "cropped" or image_type.lower() == "full" else (None, None)

    elif capture_library.lower() == "bettercam":

        try:

            if cam == None:
                initialize()
            img = np.array(cam.get_latest_frame())
            if image_type.lower() == "both":
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img, img
            elif image_type.lower() == "cropped":
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img
            elif image_type.lower() == "full":
                return img
            else:
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img, img

        except:

            return None if image_type.lower() == "cropped" or image_type.lower() == "full" else (None, None)

    elif capture_library.lower() == "mss":

        try:

            full_monitor = SCT.monitors[(display + 1)]
            img = np.array(SCT.grab(full_monitor))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            if image_type.lower() == "both":
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img, img
            elif image_type.lower() == "cropped":
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img
            elif image_type.lower() == "full":
                return img
            else:
                cropped_img = img[monitor_y1:monitor_y2, monitor_x1:monitor_x2]
                return cropped_img, img

        except:

            return None if image_type.lower() == "cropped" or image_type.lower() == "full" else (None, None)


# MARK: get_screen_dimensions()
def get_screen_dimensions(display=1):
    """
    Get the dimensions of the screen.

    Parameters
    ----------
    display : int
        The index of the screen to get the dimensions of. Defaults to primary screen. Format: 1 = primary screen

    Returns
    -------
    int, int, int, int
        The dimensions of the screen. Format: (x, y, width, height)
    """
    global screen_x, screen_y, screen_width, screen_height
    monitor = SCT.monitors[display]
    screen_x = monitor["left"]
    screen_y = monitor["top"]
    screen_width = monitor["width"]
    screen_height = monitor["height"]
    return screen_x, screen_y, screen_width, screen_height


def get_screen_index(x, y):
    """
    Get the index of the screen that is closest to the given coordinates.

    Parameters
    ----------
    x : int
        The x coordinate.
    y : int
        The y coordinate.

    Returns
    -------
    int
        The index of the screen that is closest to the given coordinates. Format: 1 = primary screen
    """
    monitors = SCT.monitors
    closest_screen_index = None
    closest_distance = float('inf')
    for i, monitor in enumerate(monitors[1:]):
        center_x = (monitor["left"] + monitor["left"] + monitor["width"]) // 2
        center_y = (monitor["top"] + monitor["top"] + monitor["height"]) // 2
        distance = ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5
        if distance < closest_distance:
            closest_screen_index = i + 1
            closest_distance = distance
    return closest_screen_index


# MARK: validate_capture_area()
def validate_capture_area(display, x1, y1, x2, y2):
    """
    Validate the capture area, ensuring that it is within the bounds of the screen.

    Parameters
    ----------
    display : int
        The index of the screen to validate the capture area for. Format: 1 = primary screen
    x1 : int
        The x coordinate of the top-left corner of the capture area.
    y1 : int
        The y coordinate of the top-left corner of the capture area.
    x2 : int
        The x coordinate of the bottom-right corner of the capture area.
    y2 : int
        The y coordinate of the bottom-right corner of the capture area.

    Returns
    -------
    int, int, int, int
        The validated capture area. Format: (x1, y1, x2, y2)
    """
    monitor = SCT.monitors[display]
    width, height = monitor["width"], monitor["height"]
    x1 = max(0, min(width - 1, x1))
    x2 = max(0, min(width - 1, x2))
    y1 = max(0, min(height - 1, y1))
    y2 = max(0, min(height - 1, y2))
    if x1 == x2:
        if x1 == 0:
            x2 = width - 1
        else:
            x1 = 0
    if y1 == y2:
        if y1 == 0:
            y2 = height - 1
        else:
            y1 = 0
    return x1, y1, x2, y2


# MARK: is_foreground_window()
def is_foreground_window(name="", blacklist=[""]):
    """
    Check if the given window is in the foreground/is focused. The window name must contain 'name' and all items in 'blacklist' must not be in the window name.

    Parameters
    ----------
    name : str
        The text which must be in the window name.
    blacklist : list
        A list of strings that must not be in the window name.

    Returns
    -------
    bool
        True if the window is in the foreground/is focused, False otherwise.
    """
    key = f"{name}{blacklist}"
    if key not in last_foreground_windows:
        last_foreground_windows[key] = [0, screen_x, screen_y, screen_x + screen_width, screen_y + screen_height]
    if last_foreground_windows[key][0] + 1 < time.time():
        hwnd = None
        top_windows = []
        is_foreground = last_foreground_windows[key][1]
        win32gui.EnumWindows(lambda hwnd, top_windows: top_windows.append((hwnd, win32gui.GetWindowText(hwnd))), top_windows)
        for hwnd, window_text in top_windows:
            if name in window_text and all(blacklist_item not in window_text for blacklist_item in blacklist):
                is_foreground = (hwnd == win32gui.GetForegroundWindow())
                break
        last_foreground_windows[key] = time.time(), is_foreground
        return is_foreground
    else:
        return last_foreground_windows[key][1]


# MARK: get_window_position()
def get_window_position(name="", blacklist=[""]):
    """
    Get the position of the given window. The window name must contain 'name' and all items in 'blacklist' must not be in the window name.

    Parameters
    ----------
    name : str
        The text which must be in the window name.
    blacklist : list
        A list of strings that must not be in the window name.

    Returns
    -------
    int, int, int, int
        The position of the window. Format: (x, y, width, height)
    """
    global last_window_positions
    key = f"{name}{blacklist}"
    if key not in last_window_positions:
        last_window_positions[key] = [0, screen_x, screen_y, screen_x + screen_width, screen_y + screen_height]
    if last_window_positions[key][0] + 1 < time.time():
        hwnd = None
        top_windows = []
        window = last_window_positions[key][1], last_window_positions[key][2], last_window_positions[key][3], last_window_positions[key][4]
        win32gui.EnumWindows(lambda hwnd, top_windows: top_windows.append((hwnd, win32gui.GetWindowText(hwnd))), top_windows)
        for hwnd, window_text in top_windows:
            if name in window_text and all(blacklist_item not in window_text for blacklist_item in blacklist):
                RECT = win32gui.GetClientRect(hwnd)
                top_left = win32gui.ClientToScreen(hwnd, (RECT[0], RECT[1]))
                bottom_right = win32gui.ClientToScreen(hwnd, (RECT[2], RECT[3]))
                window = (top_left[0], top_left[1], bottom_right[0] - top_left[0], bottom_right[1] - top_left[1])
                break
        last_window_positions[key] = time.time(), window[0], window[1], window[0] + window[2], window[1] + window[3]
        return window[0], window[1], window[0] + window[2], window[1] + window[3]
    else:
        return last_window_positions[key][1], last_window_positions[key][2], last_window_positions[key][3], last_window_positions[key][4]


# MARK: track_window()
def track_window(name="", blacklist=[""], rate=2):
    """
    Automatically update the screen and area which were set with initialize(). The window name must contain 'name' and all items in 'blacklist' must not be in the window name.

    Parameters
    ----------
    name : str
        The text which must be in the window name.
    blacklist : list
        A list of strings that must not be in the window name.
    rate : int
        The update rate in Hz, defaults to 2.

    Returns
    -------
    None
    """
    key = f"{name}{blacklist}"
    if key not in last_track_window_updates:
        last_track_window_updates[key] = 0
    if rate > 0:
        if last_track_window_updates[key] + 1/rate > time.time():
            return
    global stop_windows_capture, monitor_x1, monitor_y1, monitor_x2, monitor_y2
    x1, y1, x2, y2 = get_window_position(name=name, blacklist=blacklist)
    screen_x, screen_y, _, _ = get_screen_dimensions(get_screen_index((x1 + x2) / 2, (y1 + y2) / 2))
    if monitor_x1 != x1 - screen_x or monitor_y1 != y1 - screen_y or monitor_x2 != x2 - screen_x or monitor_y2 != y2 - screen_y:
        screen_index = get_screen_index((x1 + x2) / 2, (y1 + y2) / 2)
        if display != screen_index - 1:
            if capture_library == "WindowsCapture":
                stop_windows_capture = True
                while stop_windows_capture == True:
                    time.sleep(0.01)
            initialize(screen=screen_index - 1)
        monitor_x1, monitor_y1, monitor_x2, monitor_y2 = validate_capture_area(screen_index, x1 - screen_x, y1 - screen_y, x2 - screen_x, y2 - screen_y)
    last_track_window_updates[key] = time.time()