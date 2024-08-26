import src.variables as variables
import cv2


foreground_window = False
frame_width = None
frame_height = None
mouse_x = None
mouse_y = None
left_clicked = False
right_clicked = False
last_left_clicked = False
last_right_clicked = False


def GetTextSize(text="NONE", text_width=100, fontsize=variables.FONT_SIZE):
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
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


def Label(text="NONE", x1=0, y1=0, x2=100, y2=100, fontsize=variables.FONT_SIZE, text_color=variables.TEXT_COLOR):
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    text, fontscale, thickness, width, height = GetTextSize(text, round((x2-x1)), fontsize)
    cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, text_color, thickness, cv2.LINE_AA)


def Button(text="NONE", x1=0, y1=0, x2=100, y2=100, fontsize=variables.FONT_SIZE, round_corners=5, button_selected=False, text_color=variables.TEXT_COLOR, button_color=variables.BUTTON_COLOR, button_hover_color=variables.BUTTON_HOVER_COLOR, button_selected_color=variables.BUTTON_SELECTED_COLOR, button_selected_hover_color=variables.BUTTON_SELECTED_HOVER_COLOR):
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 and foreground_window:
        button_hovered = True
    else:
        button_hovered = False 
    if button_selected == True:
        if button_hovered == True:
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), button_selected_hover_color, round_corners, cv2.LINE_AA)
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), button_selected_hover_color, -1, cv2.LINE_AA)
        else:
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), button_selected_color, round_corners, cv2.LINE_AA)
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), button_selected_color, -1, cv2.LINE_AA)
    elif button_hovered == True:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), button_hover_color, round_corners, cv2.LINE_AA)
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), button_hover_color, -1, cv2.LINE_AA)
    else:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), button_color, round_corners, cv2.LINE_AA)
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), button_color, -1, cv2.LINE_AA)
    text, fontscale, thickness, width, height = GetTextSize(text, round((x2-x1)), fontsize)
    cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, text_color, thickness, cv2.LINE_AA)
    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 and left_clicked == False and last_left_clicked == True:
        return True, button_hovered
    else:
        return False, button_hovered