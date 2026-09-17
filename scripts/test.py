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


def initialize():
    global telemetry
    screen_capture.initialize()
    telemetry = scsTelemetry()


def main():
    initialize()

    while True:
        current_time = time.perf_counter()

        telemetry_data = telemetry.update()
        if telemetry_data["pause"] == True: return False
        if telemetry_data["sdkActive"] == False: return False

        screen_capture.track_window(name="Truck Simulator", blacklist=["Discord"])
        frame = screen_capture.capture("cropped")

        if type(frame) == type(None): return False
        if frame.shape[0] <= 0 or frame.shape[1] <= 0: return False

        telemetry_data = telemetry.update()


        cv2.imshow("frame", frame)
        cv2.waitKey(1)

if __name__ == "__main__":
    main()