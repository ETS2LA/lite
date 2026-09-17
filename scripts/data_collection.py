from ctypes import windll, byref, sizeof, c_int
from modules.telemetry import scsTelemetry
import modules.capture as screen_capture
import numpy as np
import threading
import keyboard
import win32gui
import time
import cv2
import os


path = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/") + "/dataset"
if not os.path.exists(path): os.makedirs(path)

capture_enabled = False
capture_successful = True

last_capture_time = 0.0
capture_frequency = 1.0

key = "y"
last_key_pressed = False


def initialize():
    global telemetry
    screen_capture.initialize()
    telemetry = scsTelemetry()


def capture():
    telemetry_data = telemetry.update()
    if telemetry_data["pause"] == True: return False
    if telemetry_data["sdkActive"] == False: return False

    screen_capture.track_window(name="Truck Simulator", blacklist=["Discord"])
    frame = screen_capture.capture("cropped")

    if type(frame) == type(None): return False
    if frame.shape[0] <= 0 or frame.shape[1] <= 0: return False

    telemetry_data = telemetry.update()

    file_name = f"{path}/data_{str(round(time.time(), 2)).replace('.', '_')}.npz"
    np.savez_compressed(file_name, telemetry_data=telemetry_data, frame=frame)

    # last second abort
    if capture_enabled == False:
        os.remove(file_name)
        return False

    return True


def check_key():
    global capture_enabled, last_key_pressed
    while True:
        key_pressed = keyboard.is_pressed(key)
        if key_pressed and not last_key_pressed:
            capture_enabled = not capture_enabled
        last_key_pressed = key_pressed
        time.sleep(0.05)


def capture_info():
    frame = np.zeros((75, 350, 3), dtype=np.uint8)

    window_handle = None
    state_color = (0, 0, 255)
    last_capture_state = False
    last_successful_state = True

    frame[:] = state_color
    while True:
        if last_capture_state != capture_enabled or last_successful_state != capture_successful:
            last_capture_state = capture_enabled
            last_successful_state = capture_successful
            if capture_enabled and capture_successful:
                state_color = (0, 255, 0)
            elif capture_enabled:
                state_color = (0, 255, 255)
            else:
                state_color = (0, 0, 255)
            frame[:] = state_color
            windll.dwmapi.DwmSetWindowAttribute(window_handle, 35, byref(c_int((state_color[0] << 16) | (state_color[1] << 8) | state_color[2])), sizeof(c_int))

        temp_frame = frame.copy()
        cv2.putText(
            temp_frame,
            f"Time to capture: {max(0, capture_frequency - (time.perf_counter() - last_capture_time)):.1f}",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 0) if capture_enabled else (255, 255, 255),
            2
        )

        try:
            cv2.getWindowImageRect("Capture Info")
        except:
            cv2.namedWindow("Capture Info", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Capture Info", frame.shape[1], frame.shape[0])
            cv2.setWindowProperty("Capture Info", cv2.WND_PROP_TOPMOST, 1)
            window_handle = win32gui.FindWindow(None, "Capture Info")
            windll.dwmapi.DwmSetWindowAttribute(window_handle, 35, byref(c_int((state_color[0] << 16) | (state_color[1] << 8) | state_color[2])), sizeof(c_int))

        cv2.imshow("Capture Info", temp_frame)
        cv2.waitKey(1)
        time.sleep(0.05)


def main():
    global last_capture_time, capture_successful

    threading.Thread(target=check_key, daemon=True).start()
    threading.Thread(target=capture_info, daemon=True).start()
    initialize()

    while True:
        current_time = time.perf_counter()

        if capture_enabled:
            if current_time - last_capture_time >= capture_frequency:
                last_capture_time = current_time
                capture_successful = capture()
        else:
            last_capture_time = current_time - capture_frequency

        time.sleep(0.01)

if __name__ == "__main__":
    main()