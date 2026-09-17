import datetime
print(f"\n----------------------------------------------\n\n\033[90m[{datetime.datetime.now().strftime('%H:%M:%S')}] \033[0mImporting libraries...")

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from torch.utils.tensorboard import SummaryWriter
from torch.utils.data import Dataset, DataLoader
import torch.optim.lr_scheduler as lr_scheduler
from torch.amp import GradScaler, autocast
from torchvision import transforms
import torch.optim as optim
import multiprocessing
import torch.nn as nn
from PIL import Image
import numpy as np
import threading
import random
import shutil
import torch
import time
import timm
import cv2

PATH = os.path.dirname(__file__)
DATA_PATH = PATH + "\\dataset_processed"
MODEL_PATH = PATH + "\\models"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

NUM_EPOCHS = 25
BATCH_SIZE = 64
IMG_WIDTH = 224
IMG_HEIGHT = 224
NUM_OUTPUTS = 1
COLOR_FORMAT = "BGR"
COLOR_CHANNELS = 3
LEARNING_RATE = 0.0001
WEIGHT_DECAY = 0.00001
TRAIN_VAL_RATIO = 0.9
NUM_WORKERS = 0
DROPOUT = 0.2
SHUFFLE = True
PIN_MEMORY = True
DROP_LAST = True
CACHE = True
SEED = 42

IMG_COUNT = 0
for file in os.listdir(DATA_PATH):
    if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
        IMG_COUNT += 1
if IMG_COUNT == 0:
    print("No images found, exiting...")
    exit()

random.seed(SEED)
torch.manual_seed(SEED)

RED = "\033[91m"
GREEN = "\033[92m"
DARK_GREY = "\033[90m"
NORMAL = "\033[0m"
def timestamp():
    return DARK_GREY + f"[{datetime.datetime.now().strftime('%H:%M:%S')}] " + NORMAL

print("\n----------------------------------------------\n")

print(timestamp() + f"Using {str(DEVICE).upper()} for training")
print(timestamp() + "Number of CPU cores:", multiprocessing.cpu_count())
print()
print(timestamp() + "Training settings:")
print(timestamp() + "> Epochs:", NUM_EPOCHS)
print(timestamp() + "> Batch size:", BATCH_SIZE)
print(timestamp() + "> Images:", IMG_COUNT)
print(timestamp() + "> Image width:", IMG_WIDTH)
print(timestamp() + "> Image height:", IMG_HEIGHT)
print(timestamp() + "> Color format:", COLOR_FORMAT)
print(timestamp() + "> Color channels:", COLOR_CHANNELS)
print(timestamp() + "> Learning rate:", LEARNING_RATE)
print(timestamp() + "> Weight decay:", WEIGHT_DECAY)
print(timestamp() + "> Dataset split:", TRAIN_VAL_RATIO)
print(timestamp() + "> Number of workers:", NUM_WORKERS)
print(timestamp() + "> Dropout:", DROPOUT)
print(timestamp() + "> Shuffle:", SHUFFLE)
print(timestamp() + "> Pin memory:", PIN_MEMORY)
print(timestamp() + "> Drop last:", DROP_LAST)
print(timestamp() + "> Cache: ", CACHE)
print(timestamp() + "> Seed:", SEED)


if CACHE:
    def load_data(files=None, type=None):
        images = []
        labels = []
        print(f"\r{timestamp()}Caching {type} dataset...           ", end="", flush=True)
        for file in os.listdir(DATA_PATH):
            if file in files:
                img = cv2.imread(os.path.join(DATA_PATH, file), cv2.IMREAD_COLOR_BGR)
                img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))
                img = img / 255.0

                labels_file = os.path.join(DATA_PATH, file.replace(file.split(".")[-1], "txt"))
                if os.path.exists(labels_file):
                    with open(labels_file, "r") as f:
                        label = float(f.read()) * 30
                    images.append(img)
                    labels.append(label)
                else:
                    pass
            if len(images) % round(len(files) / 100) == 0:
                print(f"\r{timestamp()}Caching {type} dataset... ({round(100 * len(images) / len(files))}%)", end="", flush=True)
        return np.array(images, dtype=np.float32), np.array(labels, dtype=np.float32)

    class CustomDataset(Dataset):
        def __init__(self, images, labels, transform=None):
            self.images = images
            self.labels = labels
            self.transform = transform

        def __len__(self):
            return len(self.images)

        def __getitem__(self, idx):
            image = self.images[idx]
            label = self.labels[idx]
            image = self.transform(image)
            label_tensor = torch.as_tensor(label, dtype=torch.float32).unsqueeze(0)
            return image, label_tensor

else:

    class CustomDataset(Dataset):
        def __init__(self, files, transform=None):
            self.files = files
            self.transform = transform

        def __len__(self):
            return len(self.files)

        def __getitem__(self, idx):
            file = self.files[idx]
            img = cv2.imread(os.path.join(DATA_PATH, file), cv2.IMREAD_COLOR_BGR)
            img = np.array(img, dtype=np.float32)
            img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))
            img = img / 255.0

            labels_file = os.path.join(DATA_PATH, file.replace(file.split(".")[-1], "txt"))

            with open(labels_file, "r") as f:
                label = float(f.read()) * 30

            if self.transform:
                img = self.transform(img)

            label_tensor = torch.as_tensor(label, dtype=torch.float32).unsqueeze(0)
            return img, label_tensor


def main():
    model = timm.create_model(
        "vit_small_patch16_224",
        pretrained=True,
        num_classes=NUM_OUTPUTS,
        img_size=(IMG_HEIGHT, IMG_WIDTH),
    ).to(DEVICE)

    def get_model_size_mb(model):
        total_params = 0
        for param in model.parameters():
            total_params += np.prod(param.size())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        non_trainable_params = total_params - trainable_params
        bytes_per_param = next(model.parameters()).element_size()
        model_size_mb = (total_params * bytes_per_param) / (1024 ** 2)
        return total_params, trainable_params, non_trainable_params, model_size_mb

    total_params, trainable_params, non_trainable_params, model_size_mb = get_model_size_mb(model)

    print()
    print(timestamp() + "Model properties:")
    print(timestamp() + f"> Total parameters: {total_params}")
    print(timestamp() + f"> Trainable parameters: {trainable_params}")
    print(timestamp() + f"> Non-trainable parameters: {non_trainable_params}")
    print(timestamp() + f"> Predicted model size: {model_size_mb:.2f}MB")

    print("\n----------------------------------------------\n")

    print(timestamp() + "Loading...")

    if not os.path.exists(f"{PATH}/logs"):
        os.makedirs(f"{PATH}/logs")
    for obj in os.listdir(f"{PATH}/logs"):
        try:
            shutil.rmtree(f"{PATH}/logs/{obj}")
        except:
            os.remove(f"{PATH}/logs/{obj}")
    summary_writer = SummaryWriter(f"{PATH}/logs", comment="Classification-Training", flush_secs=20)


    train_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.RandomRotation(5),
        transforms.RandomPerspective(0.1),
        transforms.RandomCrop((round(IMG_HEIGHT * random.uniform(0.8, 1)), round(IMG_WIDTH * random.uniform(0.8, 1)))),
        transforms.Resize((IMG_HEIGHT, IMG_WIDTH)),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1)
    ])

    val_transform = transforms.Compose([
        transforms.ToTensor()
    ])


    all_files = [f for f in os.listdir(DATA_PATH) if (f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg")) and os.path.exists(f"{DATA_PATH}/{f.replace(f.split('.')[-1], 'txt')}")]
    random.shuffle(all_files)
    train_size = int(len(all_files) * TRAIN_VAL_RATIO)
    val_size = len(all_files) - train_size
    train_files = all_files[:train_size]
    val_files = all_files[train_size:]

    if CACHE:
        train_images, train_labels = load_data(train_files, "train")
        val_images, val_labels = load_data(val_files, "val")
        train_dataset = CustomDataset(train_images, train_labels, transform=train_transform)
        val_dataset = CustomDataset(val_images, val_labels, transform=val_transform)
    else:
        train_dataset = CustomDataset(train_files, transform=train_transform)
        val_dataset = CustomDataset(val_files, transform=val_transform)

    train_dataloader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=SHUFFLE, num_workers=NUM_WORKERS, pin_memory=PIN_MEMORY, drop_last=DROP_LAST)
    val_dataloader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=SHUFFLE, num_workers=NUM_WORKERS, pin_memory=PIN_MEMORY, drop_last=DROP_LAST)

    scaler = GradScaler(device=str(DEVICE))
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = lr_scheduler.OneCycleLR(optimizer, max_lr=LEARNING_RATE, steps_per_epoch=len(train_dataloader), epochs=NUM_EPOCHS)

    print(f"\r{timestamp()}Starting training...                ")
    print("\n-----------------------------------------------------------------------------------------------------------\n")

    training_time_prediction = time.time()
    training_start_time = time.time()
    epoch_total_time = 0
    training_loss = 0
    validation_loss = 0
    training_epoch = 0

    global PROGRESS_PRINT
    PROGRESS_PRINT = "initializing"
    def training_progress_print():
        global PROGRESS_PRINT
        def num_to_str(num: int):
            str_num = format(num, ".15f")
            while len(str_num) > 15:
                str_num = str_num[:-1]
            while len(str_num) < 15:
                str_num = str_num + "0"
            return str_num
        while PROGRESS_PRINT == "initializing":
            time.sleep(1)
        last_message = ""
        while PROGRESS_PRINT == "running":
            progress = (time.time() - epoch_total_start_time) / epoch_total_time
            if progress > 1: progress = 1
            if progress < 0: progress = 0
            progress = "█" * round(progress * 10) + "░" * (10 - round(progress * 10))
            epoch_time = round(epoch_total_time, 2) if epoch_total_time > 1 else round((epoch_total_time) * 1000)
            eta = time.strftime("%H:%M:%S", time.gmtime(round((training_time_prediction - training_start_time) / (training_epoch) * NUM_EPOCHS - (training_time_prediction - training_start_time) + (training_time_prediction - time.time()), 2)))
            message = f"{progress} Epoch {training_epoch}, Train Loss: {num_to_str(training_loss)}, Val Loss: {num_to_str(validation_loss)}, {epoch_time}{'s' if epoch_total_time > 1 else 'ms'}/Epoch, ETA: {eta}"
            print(f"\r{message}" + (" " * (len(last_message) - len(message)) if len(last_message) > len(message) else ""), end="", flush=True)
            last_message = message
            time.sleep(1)
        if PROGRESS_PRINT == "finished":
            message = f"Finished at Epoch {training_epoch}, Train Loss: {num_to_str(training_loss)}, Val Loss: {num_to_str(validation_loss)}"
            print(f"\r{message}" + (" " * (len(last_message) - len(message)) if len(last_message) > len(message) else ""), end="", flush=True)
        PROGRESS_PRINT = "received"
    threading.Thread(target=training_progress_print, daemon=True).start()

    for epoch, _ in enumerate(range(NUM_EPOCHS), 1):
        epoch_total_start_time = time.time()


        epoch_training_start_time = time.time()

        model.train()
        running_training_loss = 0.0
        for i, data in enumerate(train_dataloader, 0):
            inputs, labels = data[0].to(DEVICE, non_blocking=True), data[1].to(DEVICE, non_blocking=True)
            optimizer.zero_grad()
            with autocast(device_type=str(DEVICE), dtype=torch.bfloat16):
                outputs = model(inputs)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            running_training_loss += loss.item()
        running_training_loss /= len(train_dataloader)
        training_loss = running_training_loss

        epoch_training_time = time.time() - epoch_training_start_time


        epoch_validation_start_time = time.time()

        model.eval()
        running_validation_loss = 0.0
        with torch.no_grad(), autocast(device_type=str(DEVICE), dtype=torch.bfloat16):
            for i, data in enumerate(val_dataloader, 0):
                inputs, labels = data[0].to(DEVICE, non_blocking=True), data[1].to(DEVICE, non_blocking=True)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                running_validation_loss += loss.item()
        running_validation_loss /= len(val_dataloader)
        validation_loss = running_validation_loss

        epoch_validation_time = time.time() - epoch_validation_start_time


        epoch_total_time = time.time() - epoch_total_start_time

        summary_writer.add_scalars(f"Stats", {
            "train_loss": training_loss,
            "validation_loss": validation_loss,
            "epoch_total_time": epoch_total_time,
            "epoch_training_time": epoch_training_time,
            "epoch_validation_time": epoch_validation_time
        }, epoch)

        training_epoch = epoch
        training_time_prediction = time.time()
        PROGRESS_PRINT = "running"

    PROGRESS_PRINT = "finished"
    while PROGRESS_PRINT != "received":
        time.sleep(1)

    print("\n\n-----------------------------------------------------------------------------------------------------------")

    TRAINING_TIME = time.strftime("%H-%M-%S", time.gmtime(time.time() - training_start_time))
    TRAINING_DATE = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    print()
    print(timestamp() + f"Training completed after " + TRAINING_TIME.replace("-", ":"))

    print(timestamp() + "Saving the model...")

    torch.cuda.empty_cache()

    model.eval()
    total_train = 0
    correct_train = 0
    with torch.no_grad():
        for data in train_dataloader:
            images, labels = data
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total_train += labels.size(0)
            correct_train += (predicted == torch.argmax(labels, dim=1)).sum().item()
    training_dataset_accuracy = str(round(100 * (correct_train / total_train), 2)) + "%"

    torch.cuda.empty_cache()

    total_val = 0
    correct_val = 0
    with torch.no_grad():
        for data in val_dataloader:
            images, labels = data
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total_val += labels.size(0)
            correct_val += (predicted == torch.argmax(labels, dim=1)).sum().item()
    validation_dataset_accuracy = str(round(100 * (correct_val / total_val), 2)) + "%"

    metadata_optimizer = str(optimizer).replace("\n", "")
    metadata_criterion = str(criterion).replace("\n", "")
    metadata_model = str(model).replace("\n", "")
    metadata = (f"epochs#{epoch}",
                f"batch#{BATCH_SIZE}",
                f"outputs#{NUM_OUTPUTS}",
                f"image_count#{IMG_COUNT}",
                f"image_width#{IMG_WIDTH}",
                f"image_height#{IMG_HEIGHT}",
                f"color_format#{COLOR_FORMAT}",
                f"color_channels#{COLOR_CHANNELS}",
                f"learning_rate#{LEARNING_RATE}",
                f"weight_decay#{WEIGHT_DECAY}",
                f"dataset_split#{TRAIN_VAL_RATIO}",
                f"number_of_workers#{NUM_WORKERS}",
                f"dropout#{DROPOUT}",
                f"shuffle#{SHUFFLE}",
                f"pin_memory#{PIN_MEMORY}",
                f"drop_last#{DROP_LAST}",
                f"cache#{CACHE}",
                f"seed#{SEED}",
                f"training_time#{TRAINING_TIME}",
                f"training_date#{TRAINING_DATE}",
                f"training_device#{DEVICE}",
                f"training_os#{os.name}",
                f"architecture#{metadata_model}",
                f"torch_version#{torch.__version__}",
                f"numpy_version#{np.__version__}",
                f"pil_version#{Image.__version__}",
                f"train_transform#{train_transform}",
                f"val_transform#{val_transform}",
                f"optimizer#{metadata_optimizer}",
                f"loss_function#{metadata_criterion}",
                f"training_size#{train_size}",
                f"validation_size#{val_size}",
                f"training_loss#{training_loss}",
                f"validation_loss#{validation_loss}",
                f"training_dataset_accuracy#{training_dataset_accuracy}",
                f"validation_dataset_accuracy#{validation_dataset_accuracy}")
    metadata = {"data": metadata}
    metadata = {data: str(value).encode("ascii") for data, value in metadata.items()}

    model_saved = False
    for i in range(5):
        try:
            model = torch.jit.script(model)
            torch.jit.save(model, os.path.join(MODEL_PATH, f"ClassificationModel-{TRAINING_DATE}.pt"), _extra_files=metadata)
            model_saved = True
            break
        except:
            print(timestamp() + "Failed to save the model. Retrying...")
    print(timestamp() + "Model saved successfully.") if model_saved else print(timestamp() + "Failed to save the model.")

    print("\n----------------------------------------------\n")

if __name__ == "__main__":
    main()