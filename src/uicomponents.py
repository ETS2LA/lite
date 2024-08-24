import src.variables as variables
import cv2


frame_width = None
frame_height = None
mouse_x = None
mouse_y = None
left_clicked = False
right_clicked = False
last_left_clicked = False
last_right_clicked = False


def GetTextSize(text="NONE", text_width=100, fontsize=12):
    global frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    fontscale = 1
    textsize, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, 1)
    width_current_text, height_current_text = textsize
    max_count_current_text = 3
    while width_current_text != text_width or height_current_text > fontsize:
        fontscale *= min(text_width / textsize[0], fontsize / textsize[1])
        textsize, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontscale, 1)
        max_count_current_text -= 1
        if max_count_current_text <= 0:
            break
    thickness = round(fontscale * 2)
    if thickness <= 0:
        thickness = 1
    return text, fontscale, thickness, textsize[0], textsize[1]


def Label(text="NONE", x1=0, y1=0, x2=100, y2=100, textcolor=(255, 255, 255), fontsize=12):
    global frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    text, fontscale, thickness, width, height = GetTextSize(text, round((x2-x1)), fontsize)
    cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, textcolor, thickness, cv2.LINE_AA)


def Button(text="NONE", x1=0, y1=0, x2=100, y2=100, round_corners=5, buttoncolor=(100, 100, 100), buttonhovercolor=(130, 130, 130), buttonselectedcolor=(160, 160, 160), buttonselectedhovercolor=(190, 190, 190), buttonselected=False, textcolor=(255, 255, 255), fontsize=12):
    global frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2:
        buttonhovered = True
    else:
        buttonhovered = False
    if buttonselected == True:
        if buttonhovered == True:
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), buttonselectedhovercolor, round_corners, cv2.LINE_AA)
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), buttonselectedhovercolor, -1, cv2.LINE_AA)
        else:
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), buttonselectedcolor, round_corners, cv2.LINE_AA)
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), buttonselectedcolor, -1, cv2.LINE_AA)
    elif buttonhovered == True:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), buttonhovercolor, round_corners, cv2.LINE_AA)
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), buttonhovercolor, -1, cv2.LINE_AA)
    else:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), buttoncolor, round_corners, cv2.LINE_AA)
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), buttoncolor, -1, cv2.LINE_AA)
    text, fontscale, thickness, width, height = GetTextSize(text, round((x2-x1)), fontsize)
    cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, textcolor, thickness, cv2.LINE_AA)
    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 and left_clicked == False and last_left_clicked == True:
        return True, buttonhovered
    else:
        return False, buttonhovered