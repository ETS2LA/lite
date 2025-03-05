from modules.TruckSimAPI.main import scsTelemetry as SCSTelemetry
from modules.SDKController.main import SCSController
import modules.ScreenCapture.main as ScreenCapture
import modules.ShowImage.main as ShowImage
import src.settings as settings
import src.pytorch as pytorch
import plugins.AR.main as AR
import numpy as np
import keyboard
import time
import cv2


def Initialize():
    global Enabled
    global EnableKey
    global EnableKeyPressed
    global LastEnableKeyPressed
    global SteeringHistory

    global LastIndicatorLeft
    global LastIndicatorRight
    global IndicatorLeftWaitForResponse
    global IndicatorRightWaitForResponse
    global IndicatorLeftResponseTimer
    global IndicatorRightResponseTimer

    global Identifier

    global SDKController
    global TruckSimAPI

    Enabled = True
    EnableKey = settings.Get("Controls", "Steering", "n")
    EnableKeyPressed = False
    LastEnableKeyPressed = False
    SteeringHistory = []

    LastIndicatorLeft = False
    LastIndicatorRight = False
    IndicatorLeftWaitForResponse = False
    IndicatorRightWaitForResponse = False
    IndicatorLeftResponseTimer = 0
    IndicatorRightResponseTimer = 0

    Identifier = pytorch.Initialize(Owner="OleFranz", Model="NavigationDetectionAI", Folder="model")
    pytorch.Load(Identifier)

    SDKController = SCSController()
    TruckSimAPI = SCSTelemetry()

    ScreenCapture.Initialize()
    ShowImage.Initialize(Name="NavigationDetectionAI", TitleBarColor=(0, 0, 0))


def GetTextSize(text="NONE", text_width=100, max_text_height=100):
    fontscale = 1
    textsize, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, 1)
    width_current_text, height_current_text = textsize
    max_count_current_text = 3
    while width_current_text != text_width or height_current_text > max_text_height:
        fontscale *= min(text_width / textsize[0], max_text_height / textsize[1])
        textsize, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, 1)
        max_count_current_text -= 1
        if max_count_current_text <= 0:
            break
    thickness = round(fontscale * 2)
    if thickness <= 0:
        thickness = 1
    return text, fontscale, thickness, textsize[0], textsize[1]

def preprocess_image(image):
    image = np.array(image)
    image = cv2.resize(image, (pytorch.MODELS[Identifier]["IMG_WIDTH"], pytorch.MODELS[Identifier]["IMG_HEIGHT"]))
    image = np.array(image, dtype=np.float32) / 255.0
    transform = pytorch.transforms.Compose([
        pytorch.transforms.ToTensor(),
    ])
    return transform(image).unsqueeze(0).to(pytorch.MODELS[Identifier]["Device"])


def Run(Data):
    CurrentTime = time.time()

    global Enabled
    global EnableKey
    global EnableKeyPressed
    global LastEnableKeyPressed

    global LastIndicatorLeft
    global LastIndicatorRight
    global IndicatorLeftWaitForResponse
    global IndicatorRightWaitForResponse
    global IndicatorLeftResponseTimer
    global IndicatorRightResponseTimer

    global SDKController
    global TruckSimAPI

    APIDATA = TruckSimAPI.update()
    Frame = ScreenCapture.Capture(ImageType="cropped")

    ScreenCapture.TrackWindowRouteAdvisor(Name="Truck Simulator", Blacklist=["Discord"])

    if pytorch.Loaded(Identifier) == False: time.sleep(0.1); return
    if type(Frame) == type(None): return

    FrameWidth = Frame.shape[1]
    FrameHeight = Frame.shape[0]
    if FrameWidth <= 0 or FrameHeight <= 0:
        return

    EnableKeyPressed = keyboard.is_pressed(EnableKey)
    if EnableKeyPressed == False and LastEnableKeyPressed == True:
        Enabled = not Enabled
    LastEnableKeyPressed = EnableKeyPressed

    cv2.rectangle(Frame, (0, 0), (round(FrameWidth/6), round(FrameHeight/3)), (0, 0, 0), -1)
    cv2.rectangle(Frame, (FrameWidth ,0), (round(FrameWidth-FrameWidth/6), round(FrameHeight/3)), (0, 0, 0), -1)
    LowerRed = np.array([0, 0, 160])
    UpperRed = np.array([110, 110, 255])
    Mask = cv2.inRange(Frame, LowerRed, UpperRed)
    FrameWithMask = cv2.bitwise_and(Frame, Frame, mask=Mask)
    Frame = cv2.cvtColor(FrameWithMask, cv2.COLOR_BGR2GRAY)

    if cv2.countNonZero(Frame) / (FrameWidth * FrameHeight) > 0.03:
        LaneDetected = True
    else:
        LaneDetected = False

    AIFrame = preprocess_image(Mask)
    Output = [[0] * pytorch.MODELS[Identifier]["OUTPUTS"]]

    if Enabled == True:
        if pytorch.MODELS[Identifier]["ModelLoaded"] == True:
            with pytorch.torch.no_grad():
                Output = pytorch.MODELS[Identifier]["Model"](AIFrame)
                Output = Output.tolist()

    Steering = float(Output[0][0]) / -30
    LeftIndicator = bool(float(Output[0][1]) > 0.15)
    RightIndicator = bool(float(Output[0][2]) > 0.15)

    if LaneDetected == False:
        Steering = 0
        LeftIndicator = False
        RightIndicator = False

    try:
        IndicatorLeft = APIDATA["truckBool"]["blinkerLeftActive"]
        IndicatorRight = APIDATA["truckBool"]["blinkerRightActive"]
    except:
        IndicatorLeft = False
        IndicatorRight = False

    if Enabled == True:
        if LeftIndicator != IndicatorLeft and IndicatorLeftWaitForResponse == False:
            SDKController.lblinker = not SDKController.lblinker
            IndicatorLeftWaitForResponse = True
            IndicatorLeftResponseTimer = CurrentTime
        if RightIndicator != IndicatorRight and IndicatorRightWaitForResponse == False:
            SDKController.rblinker = not SDKController.rblinker
            IndicatorRightWaitForResponse = True
            IndicatorRightResponseTimer = CurrentTime

        if IndicatorLeft != LastIndicatorLeft:
            IndicatorLeftWaitForResponse = False
        if IndicatorRight != LastIndicatorRight:
            IndicatorRightWaitForResponse = False
        if CurrentTime - 1 > IndicatorLeftResponseTimer:
            IndicatorLeftWaitForResponse = False
        if CurrentTime - 1 > IndicatorRightResponseTimer:
            IndicatorRightWaitForResponse = False
    LastIndicatorLeft = LeftIndicator
    LastIndicatorRight = RightIndicator

    Steering = Steering * 0.65

    SteeringHistory.append((Steering, CurrentTime))
    SteeringHistory.sort(key=lambda x: x[1])
    while CurrentTime - SteeringHistory[0][1] > 0.2:
        SteeringHistory.pop(0)
    Steering = sum(x[0] for x in SteeringHistory) / len(SteeringHistory)

    SDKController.steering = Steering

    Frame = cv2.cvtColor(Frame, cv2.COLOR_GRAY2BGR)

    Text, Fontscale, Thickness, _, TextHeight = GetTextSize(text="Enabled" if Enabled else "Disabled", text_width=FrameWidth/1.1, max_text_height=FrameHeight/11)
    cv2.putText(Frame, Text, (5, 5 + TextHeight), cv2.FONT_HERSHEY_SIMPLEX, Fontscale, (0, 255, 0) if Enabled else (0, 0, 255), Thickness, cv2.LINE_AA)

    CurrentDesired = Steering
    ActualSteering = -APIDATA["truckFloat"]["gameSteer"]

    divider = 5
    cv2.line(Frame, (int(FrameWidth/divider), int(FrameHeight - FrameHeight/10)), (int(FrameWidth/divider*(divider-1)), int(FrameHeight - FrameHeight/10)), (100, 100, 100), 6, cv2.LINE_AA)
    cv2.line(Frame, (int(FrameWidth/2), int(FrameHeight - FrameHeight/10)), (int(FrameWidth/2 + ActualSteering * (FrameWidth/2 - FrameWidth/divider)), int(FrameHeight - FrameHeight/10)), (0, 255, 100), 6, cv2.LINE_AA)
    cv2.line(Frame, (int(FrameWidth/2), int(FrameHeight - FrameHeight/10)), (int(FrameWidth/2 + (CurrentDesired if abs(CurrentDesired) < 1 else (1 if CurrentDesired > 0 else -1)) * (FrameWidth/2 - FrameWidth/divider)), int(FrameHeight - FrameHeight/10)), (0, 100, 255), 2, cv2.LINE_AA)

    ShowImage.Show("NavigationDetectionAI", Frame)