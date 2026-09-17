import numpy as np
import cv2
import os

path = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/") + "/dataset"
if not os.path.exists(path): os.makedirs(path)

destination_path = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/") + "/dataset_processed"
if not os.path.exists(destination_path): os.makedirs(destination_path)

for file in os.listdir(path):
    if file.endswith(".npz"):
        data = np.load(f"{path}/{file}", allow_pickle=True)
        telemetry_data = data["telemetry_data"].item()
        frame = data["frame"]

        cv2.imwrite(f"{destination_path}/{file.replace('.npz', '.png')}", frame)
        with open(f"{destination_path}/{file.replace('.npz', '.txt')}", "w") as f:
            f.write(str(telemetry_data["truckFloat"]["gameSteer"]))