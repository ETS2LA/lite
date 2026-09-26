from ctypes import windll, byref, sizeof, c_int
from modules.telemetry import scsTelemetry
from ets2la_capture import FrameReader
import numpy as np
import threading
import keyboard
import winsound
import win32gui
import math
import time
import cv2
import os


path = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/") + "/dataset"
if not os.path.exists(path): os.makedirs(path)

capture_enabled = False
capture_successful = True

last_capture_time = 0.0

NORMAL_DELTA = 1.0
PAUSE_DELTA = 2.0
capture_time_delta = NORMAL_DELTA

key = "y"
last_key_pressed = False
shared_frame = None

was_active = False
game_active = False
recent_saves = []
last_position_x = 0
last_position_y = 0
last_position_z = 0


def initialize():
    global reader
    global telemetry
    reader = FrameReader(True)
    telemetry = scsTelemetry()


def record_save(file_path):
    now = time.time()
    recent_saves.append((now, file_path))
    cutoff = now - (PAUSE_DELTA + 0.5)
    recent_saves[:] = [(t, p) for t, p in recent_saves if t >= cutoff]


def delete_recent_saves(window_s=PAUSE_DELTA):
    global recent_saves
    now = time.time()
    keep = []
    removed = 0
    for t, p in recent_saves:
        if now - t <= window_s:
            try:
                os.remove(p)
                removed += 1
            except FileNotFoundError:
                pass
        else:
            keep.append((t, p))
    recent_saves = keep


def capture(telemetry_data):
    global shared_frame
    global last_position_x
    global last_position_y
    global last_position_z

    frame_ = reader.get_frame()
    if frame_ is None or frame_.age_ms() > 100:
        return False

    frame = frame_.to_bgr()
    if type(frame) == type(None): return False
    if frame.shape[0] <= 0 or frame.shape[1] <= 0: return False

    truck_placement = telemetry_data.get("truckPlacement", {})
    position_x = truck_placement.get("coordinateX", 0)
    position_y = truck_placement.get("coordinateY", 0)
    position_z = truck_placement.get("coordinateZ", 0)
    if math.sqrt(
        (position_x - last_position_x) ** 2 +
        (position_y - last_position_y) ** 2 +
        (position_z - last_position_z) ** 2
    ) < 1.0:
        return False
    last_position_x = position_x
    last_position_y = position_y
    last_position_z = position_z

    file_name = f"{path}/data_{str(round(time.time(), 3)).replace('.', '_')}.npz"
    np.savez_compressed(file_name, telemetry_data=telemetry_data, frame=frame)
    record_save(file_name)

    shared_frame = frame.copy()

    return True


def check_key():
    global capture_enabled, last_key_pressed
    while True:
        key_pressed = keyboard.is_pressed(key)
        if key_pressed and not last_key_pressed:
            capture_enabled = not capture_enabled
        last_key_pressed = key_pressed
        time.sleep(0.05)


def blinker_beeper(telemetry):
    while True:
        data = telemetry.update()
        left = data.get("truckBool", {}).get("blinkerLeftActive", False)
        right = data.get("truckBool", {}).get("blinkerRightActive", False)
        active = left or right

        if game_active and active:
            winsound.Beep(800, 250)

        time.sleep(0.5)


def capture_info():
    global shared_frame

    frame = np.zeros((75, 350, 3), dtype=np.uint8)

    window_handle = None
    state_color = (0, 0, 255)
    last_capture_state = False
    last_successful_state = True
    last_game_active = False

    shared_frame = np.zeros((9, 16, 3), dtype=np.uint8)

    frame[:] = state_color
    while True:
        if (
            last_capture_state != capture_enabled
            or last_successful_state != capture_successful
            or last_game_active != game_active
        ):
            last_capture_state = capture_enabled
            last_successful_state = capture_successful
            last_game_active = game_active
            if capture_enabled and game_active and capture_successful:
                state_color = (0, 255, 0)
            elif capture_enabled:
                state_color = (0, 255, 255)
            else:
                state_color = (0, 0, 255)
            frame[:] = state_color
            windll.dwmapi.DwmSetWindowAttribute(window_handle, 35, byref(c_int((state_color[0] << 16) | (state_color[1] << 8) | state_color[2])), sizeof(c_int))

        temp_frame = frame.copy()
        if not capture_enabled:
            time_to_capture = 0.0
        elif not game_active:
            time_to_capture = capture_time_delta
        else:
            time_to_capture = max(0, capture_time_delta - (time.perf_counter() - last_capture_time))
        cv2.putText(
            temp_frame,
            f"Time to capture: {time_to_capture:.1f}",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 0) if capture_enabled else (255, 255, 255),
            2
        )

        if shared_frame is not None:
            game_frame = cv2.resize(shared_frame, (frame.shape[1], round(shared_frame.shape[0] * (temp_frame.shape[1] / shared_frame.shape[1]))))
            temp_frame = np.vstack((temp_frame, game_frame))

        try:
            cv2.getWindowImageRect("Capture Info")
        except:
            cv2.namedWindow("Capture Info", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Capture Info", temp_frame.shape[1], temp_frame.shape[0])
            cv2.setWindowProperty("Capture Info", cv2.WND_PROP_TOPMOST, 1)
            window_handle = win32gui.FindWindow(None, "Capture Info")
            windll.dwmapi.DwmSetWindowAttribute(window_handle, 35, byref(c_int((state_color[0] << 16) | (state_color[1] << 8) | state_color[2])), sizeof(c_int))

        cv2.imshow("Capture Info", temp_frame)
        cv2.waitKey(1)
        time.sleep(0.05)


def main():
    global last_capture_time, capture_successful, capture_time_delta, was_active, game_active

    initialize()
    threading.Thread(target=check_key, daemon=True).start()
    threading.Thread(target=capture_info, daemon=True).start()
    threading.Thread(target=blinker_beeper, args=(telemetry,), daemon=True).start()

    while True:
        current_time = time.perf_counter()

        telemetry_data = telemetry.update()
        if telemetry_data == {}:
            continue

        game_active = (telemetry_data.get("pause", True) == False) and (telemetry_data.get("sdkActive", False) == True)

        if was_active and not game_active:
            delete_recent_saves(PAUSE_DELTA)
            capture_time_delta = PAUSE_DELTA
            last_capture_time = current_time
        elif not was_active and game_active:
            capture_time_delta = PAUSE_DELTA
            last_capture_time = current_time
        was_active = game_active

        if capture_enabled and game_active:
            if current_time - last_capture_time >= capture_time_delta:
                last_capture_time = current_time
                capture_successful = capture(telemetry_data)
                capture_time_delta = NORMAL_DELTA
        elif capture_enabled:
            capture_time_delta = PAUSE_DELTA
            last_capture_time = current_time
        else:
            last_capture_time = current_time - capture_time_delta

        time.sleep(0.01)


if __name__ == "__main__":
    main()