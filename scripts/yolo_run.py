from ultralytics import YOLO
import cv2
import os


MODEL = "yolo26n_2026-09-10-22-00-00"

SCRIPT_DIR = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/")
WEIGHTS_PATH = f"{SCRIPT_DIR}/yolo/runs/{MODEL}/weights/best.pt"
VAL_IMAGES_DIR = f"{SCRIPT_DIR}/dataset_processed/images/val"

IOU_THRESHOLD = 0.25
CONF_THRESHOLD = 0.25
DEVICE = 0


if not os.path.exists(WEIGHTS_PATH):
    raise FileNotFoundError(f"Could not find trained weights at {WEIGHTS_PATH}")

if not os.path.exists(VAL_IMAGES_DIR):
    raise FileNotFoundError(f"Could not find val images at {VAL_IMAGES_DIR}")

model = YOLO(WEIGHTS_PATH)
class_names = model.names

print(f"Loaded model at {WEIGHTS_PATH}")

image_files = sorted(
    f for f in os.listdir(VAL_IMAGES_DIR)
    if f.lower().endswith((".png", ".jpg", ".jpeg"))
)

if not image_files:
    raise FileNotFoundError(f"No images found in {VAL_IMAGES_DIR}")

print(f"Loaded {len(image_files)} val images.")
print("Controls: [Enter] / [Space] = next image, [q] / [Esc] = quit")

cv2.namedWindow("Object detection", cv2.WINDOW_NORMAL)

idx = 0
while idx < len(image_files):
    file = image_files[idx]
    image_path = f"{VAL_IMAGES_DIR}/{file}"
    frame = cv2.imread(image_path)

    if frame is None:
        print(f"Could not read {image_path}, skipping.")
        idx += 1
        continue

    results = model.predict(
        frame,
        iou=IOU_THRESHOLD,
        conf=CONF_THRESHOLD,
        device=DEVICE,
        verbose=False
    )[0]

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        label = f"{class_names[cls_id]} {conf:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1 - text_h - 8), (x1 + text_w + 4, y1), (0, 255, 0), -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    cv2.imshow("Object detection", frame)

    key = cv2.waitKey(0) & 0xFF
    if key in (13, 32):
        idx += 1
    elif key in (27, ord("q")):
        print("Quit by user.")
        break

cv2.destroyAllWindows()