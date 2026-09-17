from ultralytics.utils import WEIGHTS_DIR
from ultralytics import YOLO
import time
import os


CLASSES = [
    "car",
    "bus",
    "truck",
    "stoplight",
    "streetlamp",
    "sign",
    "short post",
    "long pole",
    "curved pole",
    "lane line",
    "tree trunk",
    "bridge pier",
    "traffic cone",
    "traffic delineator"
]

RANDOM_SEED = 42

MODEL = "yolo26s"
EPOCHS = 100
IMGSZ = 640
BATCH = 8
DEVICE = 0
PATIENCE = 10

SCRIPT_DIR = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/")
DATASET_DIR = f"{SCRIPT_DIR}/dataset_processed"
WEIGHTS_DIR = f"{SCRIPT_DIR}/yolo/weights"
PROJECT = f"{SCRIPT_DIR}/yolo/runs"
NAME = f"{MODEL}_{time.strftime('%Y-%m-%d_%H-%M-%S')}"


if __name__ == "__main__":
    model = YOLO(f"{SCRIPT_DIR}/yolo/models/{MODEL}.pt")

    results = model.train(
        data=f"{DATASET_DIR}/data.yaml",
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        workers=0,
        project=PROJECT,
        name=NAME,
        patience=PATIENCE,
        exist_ok=True,
    )

    print("\nTraining complete.")
    print(f"Best weights saved to: {PROJECT}/{NAME}/weights/best.pt")