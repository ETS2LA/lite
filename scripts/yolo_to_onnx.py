from ultralytics import YOLO
from pathlib import Path
import shutil


MODEL = "yolo26n_2026-09-20_18-29-19"
RESOLUTION = (960, 540)

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS = ROOT / "scripts" / "yolo" / "runs" / MODEL / "weights" / "best.pt"
OUTPUT_DIR = ROOT / "scripts" / "yolo" / "models"
OUTPUT = OUTPUT_DIR / f"{MODEL}-{RESOLUTION[0]}x{RESOLUTION[1]}.onnx"


def main() -> None:
    if not WEIGHTS.is_file():
        raise FileNotFoundError(f"Could not find trained weights at {WEIGHTS}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    exported_path = YOLO(str(WEIGHTS)).export(
        format="onnx",
        imgsz=RESOLUTION[::-1],
        dynamic=False,
        simplify=True,
        nms=False,
    )
    shutil.copy2(exported_path, OUTPUT)
    print(f"Wrote ONNX model to {OUTPUT}")


if __name__ == "__main__":
    main()