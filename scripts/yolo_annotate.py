import argparse
from contextlib import nullcontext
import os
import random
import tempfile

import cv2
import numpy as np
import torch
from huggingface_hub import hf_hub_download
from PIL import Image
from safetensors.torch import load_file

from sam3 import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor


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

MODEL_REPO = "1038lab/sam3"
MODEL_FILENAME = "sam3.safetensors"
CONFIDENCE_THRESHOLD = 0.35
OVERLAP_THRESHOLD = 0.5
VAL_FRACTION = 0.10
RANDOM_SEED = 42


def parse_args():
    parser = argparse.ArgumentParser(description="Annotate NPZ frames with SAM 3.")
    parser.add_argument(
        "--device",
        default="cuda",
        choices=("cuda", "cpu"),
        help="Inference device. CUDA is the default and is required for normal use.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help="SAM 3 confidence threshold (default: %(default)s).",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Do not open the live detection preview window.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip frames whose image and label files already exist.",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Process at most this many frames; 0 means all frames.",
    )
    parser.add_argument(
        "--precision",
        choices=("fp16", "fp32"),
        default="fp16",
        help="CUDA inference precision. FP16 is recommended for 4 GiB GPUs.",
    )
    parser.add_argument(
        "--overlap-iou",
        type=float,
        default=OVERLAP_THRESHOLD,
        dest="overlap_threshold",
        help=(
            "Suppress weaker masks when their shared area covers this fraction "
            "of the smaller mask (default: %(default)s)."
        ),
    )
    return parser.parse_args()


def load_sam3(device, precision):
    if device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA was requested but torch.cuda.is_available() is false. "
                "Install the CUDA PyTorch build and verify the NVIDIA driver."
            )
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("WARNING: running SAM 3 on CPU; this will be very slow.")

    cache_root = os.path.expanduser(os.path.join("~", ".cache", "huggingface", "hub"))
    cached_checkpoints = []
    repository_cache = os.path.join(
        cache_root,
        f"models--{MODEL_REPO.replace('/', '--')}",
        "snapshots",
    )
    if os.path.isdir(repository_cache):
        for root, _, filenames in os.walk(repository_cache):
            if MODEL_FILENAME in filenames:
                cached_checkpoints.append(os.path.join(root, MODEL_FILENAME))

    if cached_checkpoints:
        checkpoint_path = max(cached_checkpoints, key=os.path.getmtime)
        checkpoint_size_gb = os.path.getsize(checkpoint_path) / (1024**3)
        print(f"Using cached SAM 3 checkpoint: {checkpoint_path}")
        print(f"Checkpoint size: {checkpoint_size_gb:.2f} GiB")
    else:
        print(f"Downloading {MODEL_REPO}/{MODEL_FILENAME}...")
        checkpoint_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILENAME,
        )

    try:
        print("Building SAM 3 model...")
        model = build_sam3_image_model(
            device=device,
            eval_mode=True,
            load_from_HF=False,
        )
        if device == "cuda" and precision == "fp16":
            print("Converting empty SAM 3 model to FP16...")
            model = model.half().eval()
            install_fp16_input_compatibility(model)
        print("Loading checkpoint tensors...")
        checkpoint = load_file(checkpoint_path, device="cpu")
        if any(key.startswith("detector.") for key in checkpoint):
            checkpoint = {
                key.removeprefix("detector."): value
                for key, value in checkpoint.items()
                if key.startswith("detector.")
            }
        missing_keys, unexpected_keys = model.load_state_dict(checkpoint, strict=False)
        del checkpoint
        if missing_keys:
            raise RuntimeError(
                f"SAM 3 checkpoint did not load correctly; missing {len(missing_keys)} "
                f"model keys, including: {missing_keys[:3]}"
            )
        if unexpected_keys:
            print(f"Warning: ignored {len(unexpected_keys)} unexpected checkpoint keys.")

        if device == "cuda" and precision == "fp32":
            print("SAM 3 is running in CUDA FP32.")
        model.eval()
    except torch.cuda.OutOfMemoryError as error:
        raise RuntimeError(
            "SAM 3 ran out of VRAM. This GPU has 4 GiB; use --device cpu or "
            "close other GPU applications before retrying."
        ) from error

    return model, Sam3Processor(
        model,
        device=device,
        confidence_threshold=CONFIDENCE_THRESHOLD,
    )


def install_fp16_input_compatibility(model):
    def cast_inputs(module, inputs):
        target_dtype = module.weight.dtype
        return tuple(
            value.to(dtype=target_dtype)
            if isinstance(value, torch.Tensor) and value.is_floating_point()
            else value
            for value in inputs
        )

    for module in model.modules():
        if isinstance(module, torch.nn.Linear):
            module.register_forward_pre_hook(cast_inputs)


def run_sam3(processor, frame_bgr, precision, overlap_threshold):
    height, width = frame_bgr.shape[:2]
    image = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    detections = []
    detection_masks = []

    device_type = torch.device(processor.device).type
    inference_context = (
        torch.amp.autocast("cuda", dtype=torch.float16)
        if device_type == "cuda" and precision == "fp16"
        else nullcontext()
    )
    with inference_context:
        state = processor.set_image(image)
        for class_id, class_name in enumerate(CLASSES):
            state = processor.set_text_prompt(prompt=class_name, state=state)
            boxes = state["boxes"].detach().float().cpu().numpy()
            masks = state["masks"].detach().bool().cpu().numpy()
            scores = state["scores"].detach().float().cpu().numpy()

            for (x1, y1, x2, y2), mask, score in zip(boxes, masks, scores):
                x1 = max(0.0, min(float(x1), width))
                x2 = max(0.0, min(float(x2), width))
                y1 = max(0.0, min(float(y1), height))
                y2 = max(0.0, min(float(y2), height))
                box_width = (x2 - x1) / width
                box_height = (y2 - y1) / height
                if box_width <= 0 or box_height <= 0:
                    continue
                detections.append(
                    (
                        class_id,
                        ((x1 + x2) / 2) / width,
                        ((y1 + y2) / 2) / height,
                        box_width,
                        box_height,
                        float(score),
                    )
                )
                detection_masks.append(mask)

    return suppress_overlapping_detections(
        detections, detection_masks, overlap_threshold=overlap_threshold
    )


def suppress_overlapping_detections(detections, masks, overlap_threshold):
    if not 0.0 < overlap_threshold <= 1.0:
        raise ValueError("overlap_threshold must be greater than 0 and at most 1")
    if len(detections) != len(masks):
        raise ValueError("detections and masks must have the same length")

    def overlap_ratio(first_mask, second_mask):
        first_mask = np.asarray(first_mask, dtype=bool).squeeze()
        second_mask = np.asarray(second_mask, dtype=bool).squeeze()
        if first_mask.shape != second_mask.shape:
            raise ValueError("all segmentation masks must have the same shape")
        intersection = np.logical_and(first_mask, second_mask).sum()
        smaller_area = min(first_mask.sum(), second_mask.sum())
        return intersection / smaller_area if smaller_area else 0.0

    kept = []
    kept_masks = []
    for detection, mask in sorted(
        zip(detections, masks), key=lambda item: item[0][5], reverse=True
    ):
        if all(
            overlap_ratio(mask, existing_mask) < overlap_threshold
            for existing_mask in kept_masks
        ):
            kept.append(detection)
            kept_masks.append(mask)
    return kept


def write_image(path, frame):
    directory = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(dir=directory, suffix=".png", delete=False) as file:
        temporary_path = file.name
    try:
        if not cv2.imwrite(temporary_path, frame):
            raise OSError(f"OpenCV could not write image: {path}")
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def write_labels(path, detections):
    directory = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="ascii", dir=directory, suffix=".txt", delete=False
    ) as file:
        temporary_path = file.name
        for class_id, xc, yc, box_width, box_height, _ in detections:
            file.write(
                f"{class_id} {xc:.6f} {yc:.6f} "
                f"{box_width:.6f} {box_height:.6f}\n"
            )
    try:
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def main():
    args = parse_args()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    dataset_path = os.path.join(script_dir, "dataset")
    destination_path = os.path.join(script_dir, "dataset_processed")
    directories = {
        "train_images": os.path.join(destination_path, "images", "train"),
        "val_images": os.path.join(destination_path, "images", "val"),
        "train_labels": os.path.join(destination_path, "labels", "train"),
        "val_labels": os.path.join(destination_path, "labels", "val"),
    }
    for directory in directories.values():
        os.makedirs(directory, exist_ok=True)

    model, processor = load_sam3(args.device, args.precision)
    processor.set_confidence_threshold(args.confidence)

    npz_files = [name for name in os.listdir(dataset_path) if name.endswith(".npz")]
    random.seed(RANDOM_SEED)
    random.shuffle(npz_files)
    n_val = max(1, int(len(npz_files) * VAL_FRACTION)) if npz_files else 0
    val_set = set(npz_files[:n_val])
    print(f"Found {len(npz_files)} NPZ files -> {len(npz_files) - n_val} train / {n_val} val")

    processed = 0
    try:
        for index, filename in enumerate(npz_files, start=1):
            basename = os.path.splitext(filename)[0]
            split = "val" if filename in val_set else "train"
            image_dir = directories[f"{split}_images"]
            label_dir = directories[f"{split}_labels"]
            image_path = os.path.join(image_dir, f"{basename}.png")
            label_path = os.path.join(label_dir, f"{basename}.txt")
            if args.resume and os.path.exists(image_path) and os.path.exists(label_path):
                print(f"[{index}/{len(npz_files)}] {filename}: skipped (already complete)")
                continue

            with np.load(os.path.join(dataset_path, filename), allow_pickle=True) as data:
                frame = data["frame"]

            detections = run_sam3(
                processor,
                frame,
                args.precision,
                args.overlap_threshold,
            )
            preview = frame.copy()
            height, width = preview.shape[:2]
            write_image(image_path, frame)
            write_labels(label_path, detections)

            for class_id, xc, yc, box_width, box_height, score in detections:
                if not args.no_preview:
                    x1 = int((xc - box_width / 2) * width)
                    y1 = int((yc - box_height / 2) * height)
                    x2 = int((xc + box_width / 2) * width)
                    y2 = int((yc + box_height / 2) * height)
                    cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        preview,
                        f"{CLASSES[class_id]} {score:.2f}",
                        (x1, max(0, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

            if not args.no_preview:
                cv2.imshow("SAM 3 labeling preview", preview)
                cv2.waitKey(1)
            processed += 1
            print(f"[{index}/{len(npz_files)}] {filename}: {len(detections)} objects labeled ({split})")
            if args.max_images and processed >= args.max_images:
                print(f"Reached --max-images={args.max_images}.")
                break
    finally:
        cv2.destroyAllWindows()

    yaml_path = os.path.join(destination_path, "data.yaml")
    with open(yaml_path, "w", encoding="ascii") as yaml_file:
        yaml_file.write(f"path: {destination_path.replace(os.sep, '/') }\n")
        yaml_file.write("train: images/train\nval: images/val\n\nnames:\n")
        for class_id, class_name in enumerate(CLASSES):
            yaml_file.write(f"  {class_id}: {class_name}\n")
    print(f"\nDone. Dataset ready at: {destination_path}")


if __name__ == "__main__":
    main()