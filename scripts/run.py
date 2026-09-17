import modules.capture as screen_capture
from torchvision import transforms
import numpy as np
import torch
import cv2
import os


def main():
    screen_capture.initialize()


    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    PATH = os.path.dirname(__file__).replace("\\", "/") + "/models"
    MODEL_PATH = ""
    models = []
    for file in os.listdir(PATH):
        if file.endswith(".pt"):
            models.append(os.path.join(PATH, file))
    if len(models) > 0:
        MODEL_PATH = max(models, key=os.path.getmtime)
    if MODEL_PATH == "":
        print("No model found.")
        exit(0)

    print(f"Model: {MODEL_PATH}")

    metadata = {"data": []}
    model: torch.jit.ScriptModule = torch.jit.load(MODEL_PATH, _extra_files=metadata, map_location=device)
    model.eval()

    key: str
    metadata = eval(metadata["data"])
    for key in metadata:
        if key.split("#")[0] == "classes":
            CLASSES = key.split("#")[1].split(",")
        elif key.split("#")[0] == "classes_count":
            CLASSES_COUNT = int(key.split("#")[1])
        elif key.split("#")[0] == "image_width":
            IMG_WIDTH = int(key.split("#")[1])
        elif key.split("#")[0] == "image_height":
            IMG_HEIGHT = int(key.split("#")[1])
        elif key.split("#")[0] == "image_channels":
            IMG_CHANNELS = str(key.split("#")[1])
        elif key.split("#")[0] == "training_dataset_accuracy":
            print("Training dataset accuracy: " + str(key.split("#")[1]))
        elif key.split("#")[0] == "validation_dataset_accuracy":
            print("Validation dataset accuracy: " + str(key.split("#")[1]))
        elif key.split("#")[0] == "val_transform":
            transform = key.replace("\\n", "\n").replace("\\", "").split("#")[1]
            transform_list = []
            transform_parts = transform.strip().split("\n")
            for part in transform_parts[1:-1]:
                part = part.strip()
                if part:
                    try:
                        transform_args = []
                        transform_name = part.split("(")[0]
                        if "(" in part:
                            args = part.split("(")[1][:-1].split(",")
                            for arg in args:
                                try:
                                    transform_args.append(int(arg.strip()))
                                except ValueError:
                                    try:
                                        transform_args.append(float(arg.strip()))
                                    except ValueError:
                                        transform_args.append(arg.strip())
                        if transform_name == "ToTensor":
                            transform_list.append(transforms.ToTensor())
                        else:
                            transform_list.append(getattr(transforms, transform_name)(*transform_args))
                    except (AttributeError, IndexError, ValueError):
                        print(f"Skipping or failed to create transform: {part}")
            transform = transforms.Compose(transform_list)


    while True:
        screen_capture.track_window(name="Truck Simulator", blacklist=["Discord"])
        frame = screen_capture.capture("cropped")
        if type(frame) == type(None): continue
        if frame.shape[0] <= 0 or frame.shape[1] <= 0: continue

        frame = np.array(frame, dtype=np.float32)
        frame = cv2.resize(frame, (IMG_WIDTH, IMG_HEIGHT))
        frame = frame / 255.0

        frame_tensor = transform(frame).unsqueeze(0).to(device)
        with torch.no_grad():
            output = np.array(model(frame_tensor)[0].tolist())
            print(output)

if __name__ == "__main__":
    main()