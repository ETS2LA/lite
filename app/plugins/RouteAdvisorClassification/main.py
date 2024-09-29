import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage
import src.variables as variables
from torchvision import transforms
import numpy as np
import torch
import time
import cv2
import os


def Initialize():
    global LastScreenCaptureCheck

    global METADATA
    global DEVICE
    global MODEL

    global IMG_WIDTH
    global IMG_HEIGHT
    global IMG_CHANNELS
    global MODEL_OUTPUTS

    LastScreenCaptureCheck = 0

    METADATA = {"data": []}
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    MODEL = None
    for file in os.listdir(variables.PATH):
        if file.endswith(".pt"):
            MODEL = torch.jit.load(f"{variables.PATH}{file}", _extra_files=METADATA, map_location=DEVICE)
            break
    if MODEL == None:
        plugins.AddToQueue({"MANAGEPLUGINS": ["RouteAdvisorClassification", "Stop"]})
        return

    METADATA = eval(METADATA["data"])

    for item in METADATA:
        item = str(item)
        if "image_width" in item:
            IMG_WIDTH = int(item.split("#")[1])
        if "image_height" in item:
            IMG_HEIGHT = int(item.split("#")[1])
        if "image_channels" in item:
            IMG_CHANNELS = str(item.split("#")[1])
        if "outputs" in item:
            MODEL_OUTPUTS = int(item.split("#")[1])

    ScreenCapture.Initialize()
    ShowImage.Initialize("RouteAdvisorClassification", (0, 0, 0))


def Run(data):
    CurrentTime = time.time()
    if MODEL == None:
        return

    global LastScreenCaptureCheck

    if LastScreenCaptureCheck + 0.5 < time.time():
        MapTopLeft, MapBottomRight, ArrowTopLeft, ArrowBottomRight = ScreenCapture.GetRouteAdvisorPosition()
        ScreenX, ScreenY, _, _ = ScreenCapture.GetScreenDimensions(ScreenCapture.GetScreenIndex((MapTopLeft[0] + MapBottomRight[0]) / 2, (MapTopLeft[1] + MapBottomRight[1]) / 2))
        if ScreenCapture.MonitorX1 != MapTopLeft[0] - ScreenX or ScreenCapture.MonitorY1 != MapTopLeft[1] - ScreenY or ScreenCapture.MonitorX2 != MapBottomRight[0] - ScreenX or ScreenCapture.MonitorY2 != MapBottomRight[1] - ScreenY:
            ScreenIndex = ScreenCapture.GetScreenIndex((MapTopLeft[0] + MapBottomRight[0]) / 2, (MapTopLeft[1] + MapBottomRight[1]) / 2)
            if ScreenCapture.Display != ScreenIndex - 1:
                if ScreenCapture.CaptureLibrary == "WindowsCapture":
                    ScreenCapture.StopWindowsCapture = True
                    while ScreenCapture.StopWindowsCapture == True:
                        time.sleep(0.01)
                ScreenCapture.Initialize()
            ScreenCapture.MonitorX1, ScreenCapture.MonitorY1, ScreenCapture.MonitorX2, ScreenCapture.MonitorY2 = ScreenCapture.ValidateCaptureArea(ScreenIndex, MapTopLeft[0] - ScreenX, MapTopLeft[1] - ScreenY, MapBottomRight[0] - ScreenX, MapBottomRight[1] - ScreenY)
        LastScreenCaptureCheck = CurrentTime

    Frame = ScreenCapture.Capture(ImageType="cropped")
    if type(Frame) == type(None) or Frame.shape[0] <= 0 or Frame.shape[1] <= 0:
        return


    image = np.array(Frame, dtype=np.float32)
    if IMG_CHANNELS == 'Grayscale' or IMG_CHANNELS == 'Binarize':
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    if IMG_CHANNELS == 'RG':
        image = np.stack((image[:, :, 0], image[:, :, 1]), axis=2)
    elif IMG_CHANNELS == 'GB':
        image = np.stack((image[:, :, 1], image[:, :, 2]), axis=2)
    elif IMG_CHANNELS == 'RB':
        image = np.stack((image[:, :, 0], image[:, :, 2]), axis=2)
    elif IMG_CHANNELS == 'R':
        image = image[:, :, 0]
        image = np.expand_dims(image, axis=2)
    elif IMG_CHANNELS == 'G':
        image = image[:, :, 1]
        image = np.expand_dims(image, axis=2)
    elif IMG_CHANNELS == 'B':
        image = image[:, :, 2]
        image = np.expand_dims(image, axis=2)
    image = cv2.resize(image, (IMG_WIDTH, IMG_HEIGHT))
    image = image / 255.0
    if IMG_CHANNELS == 'Binarize':
        image = cv2.threshold(image, 0.5, 1.0, cv2.THRESH_BINARY)[1]

    image = transforms.ToTensor()(image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        output = np.array(MODEL(image)[0].tolist())

    Values = [True if output[i] > 0.5 else False for i in range(3)]
    print(f"SideCorrect: {Values[0]}, ZoomCorrect: {Values[1]}, TabCorrect: {Values[2]}   {[round(output[i], 2) for i in range(3)]}")

    ShowImage.Show("RouteAdvisorClassification", Frame)