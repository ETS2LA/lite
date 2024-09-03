import src.variables as variables
import src.settings as settings
import math
import time
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
    y1 += variables.TITLE_BAR_HEIGHT
    y2 += variables.TITLE_BAR_HEIGHT
    texts = text.split("\n")
    line_height = ((y2-y1) / len(texts))
    for i, t in enumerate(texts):
        text, fontscale, thickness, width, height = GetTextSize(t, round((x2-x1)), line_height / 1.5 if line_height / 1.5 < fontsize else fontsize)
        cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (i + 0.5) * line_height + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, text_color, thickness, cv2.LINE_AA)


def Button(text="NONE", x1=0, y1=0, x2=100, y2=100, fontsize=variables.FONT_SIZE, round_corners=5, button_selected=False, text_color=variables.TEXT_COLOR, button_color=variables.BUTTON_COLOR, button_hover_color=variables.BUTTON_HOVER_COLOR, button_selected_color=variables.BUTTON_SELECTED_COLOR, button_selected_hover_color=variables.BUTTON_SELECTED_HOVER_COLOR):
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    y1 += variables.TITLE_BAR_HEIGHT
    y2 += variables.TITLE_BAR_HEIGHT
    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 and foreground_window and (variables.CONTEXT_MENU[0] == False or text in str(variables.CONTEXT_MENU_ITEMS)):
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


def Switch(text="NONE", x1=0, y1=0, x2=100, y2=100, switch_width=40, switch_height=20, state=False, setting=None, fontsize=variables.FONT_SIZE, text_color=variables.TEXT_COLOR, switch_color=variables.SWITCH_COLOR, switch_knob_color=variables.SWITCH_KNOB_COLOR, switch_hover_color=variables.SWITCH_HOVER_COLOR, switch_enabled_color=variables.SWITCH_ENABLED_COLOR, switch_enabled_hover_color=variables.SWITCH_ENABLED_HOVER_COLOR):
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    current_time = time.time()
    y1 += variables.TITLE_BAR_HEIGHT
    y2 += variables.TITLE_BAR_HEIGHT
    if text in variables.SWITCHES:
        state = variables.SWITCHES[text][0]
    else:
        if setting is not None:
            state = settings.Get(str(setting[0]), str(setting[1]), setting[2])
        variables.SWITCHES[text] = state, 0

    x = current_time - variables.SWITCHES[text][1]
    if x < 0.3333:
        x *= 3
        animation_state = 1 - math.pow(2, -10 * x)
        variables.RENDER_FRAME = True
        if state == False:
            switch_color = switch_color[0] * animation_state + switch_enabled_color[0] * (1 - animation_state), switch_color[1] * animation_state + switch_enabled_color[1] * (1 - animation_state), switch_color[2] * animation_state + switch_enabled_color[2] * (1 - animation_state)
            switch_hover_color = switch_hover_color[0] * animation_state + switch_enabled_hover_color[0] * (1 - animation_state), switch_hover_color[1] * animation_state + switch_enabled_hover_color[1] * (1 - animation_state), switch_hover_color[2] * animation_state + switch_enabled_hover_color[2] * (1 - animation_state)
        else:
            switch_enabled_color = switch_color[0] * (1 - animation_state) + switch_enabled_color[0] * animation_state, switch_color[1] * (1 - animation_state) + switch_enabled_color[1] * animation_state, switch_color[2] * (1 - animation_state) + switch_enabled_color[2] * animation_state
            switch_enabled_hover_color = switch_hover_color[0] * (1 - animation_state) + switch_enabled_hover_color[0] * animation_state, switch_hover_color[1] * (1 - animation_state) + switch_enabled_hover_color[1] * animation_state, switch_hover_color[2] * (1 - animation_state) + switch_enabled_hover_color[2] * animation_state
    else:
        animation_state = 1

    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 and foreground_window and (variables.CONTEXT_MENU[0] == False or text in str(variables.CONTEXT_MENU_ITEMS)):
        switch_hovered = True
    else:
        switch_hovered = False
    if switch_hovered == True:
        if state == True:
            cv2.circle(variables.FRAME, (round(x1+switch_height/2), round((y1+y2)/2)), round(switch_height/2), switch_enabled_hover_color, -1, cv2.LINE_AA)
            cv2.circle(variables.FRAME, (round(x1+switch_width-switch_height/2), round((y1+y2)/2)), round(switch_height/2), switch_enabled_hover_color, -1, cv2.LINE_AA)
            cv2.rectangle(variables.FRAME, (round(x1+switch_height/2+1), round((y1+y2)/2-switch_height/2)), (round(x1+switch_width-switch_height/2-1), round((y1+y2)/2+switch_height/2)), switch_enabled_hover_color, -1, cv2.LINE_AA)
            if animation_state < 1:
                cv2.circle(variables.FRAME, (round(x1+switch_height/2+(switch_width-switch_height)*animation_state), round((y1+y2)/2)), round(switch_height/2.5), switch_knob_color, -1, cv2.LINE_AA)
            else:
                cv2.circle(variables.FRAME, (round(x1+switch_width-switch_height/2), round((y1+y2)/2)), round(switch_height/2.5), switch_knob_color, -1, cv2.LINE_AA)
        else:
            cv2.circle(variables.FRAME, (round(x1+switch_height/2), round((y1+y2)/2)), round(switch_height/2), switch_hover_color, -1, cv2.LINE_AA)
            cv2.circle(variables.FRAME, (round(x1+switch_width-switch_height/2), round((y1+y2)/2)), round(switch_height/2), switch_hover_color, -1, cv2.LINE_AA)
            cv2.rectangle(variables.FRAME, (round(x1+switch_height/2+1), round((y1+y2)/2-switch_height/2)), (round(x1+switch_width-switch_height/2-1), round((y1+y2)/2+switch_height/2)), switch_hover_color, -1, cv2.LINE_AA)
            if animation_state < 1:
                cv2.circle(variables.FRAME, (round(x1+switch_height/2+(switch_width-switch_height)*(1-animation_state)), round((y1+y2)/2)), round(switch_height/2.5), switch_knob_color, -1, cv2.LINE_AA)
            else:
                cv2.circle(variables.FRAME, (round(x1+switch_height/2), round((y1+y2)/2)), round(switch_height/2.5), switch_knob_color, -1, cv2.LINE_AA)
    else:
        if state == True:
            cv2.circle(variables.FRAME, (round(x1+switch_height/2), round((y1+y2)/2)), round(switch_height/2), switch_enabled_color, -1, cv2.LINE_AA)
            cv2.circle(variables.FRAME, (round(x1+switch_width-switch_height/2), round((y1+y2)/2)), round(switch_height/2), switch_enabled_color, -1, cv2.LINE_AA)
            cv2.rectangle(variables.FRAME, (round(x1+switch_height/2+1), round((y1+y2)/2-switch_height/2)), (round(x1+switch_width-switch_height/2-1), round((y1+y2)/2+switch_height/2)), switch_enabled_color, -1, cv2.LINE_AA)
            if animation_state < 1:
                cv2.circle(variables.FRAME, (round(x1+switch_height/2+(switch_width-switch_height)*animation_state), round((y1+y2)/2)), round(switch_height/2.5), switch_knob_color, -1, cv2.LINE_AA)
            else:
                cv2.circle(variables.FRAME, (round(x1+switch_width-switch_height/2), round((y1+y2)/2)), round(switch_height/2.5), switch_knob_color, -1, cv2.LINE_AA)
        else:
            cv2.circle(variables.FRAME, (round(x1+switch_height/2), round((y1+y2)/2)), round(switch_height/2), switch_color, -1, cv2.LINE_AA)
            cv2.circle(variables.FRAME, (round(x1+switch_width-switch_height/2), round((y1+y2)/2)), round(switch_height/2), switch_color, -1, cv2.LINE_AA)
            cv2.rectangle(variables.FRAME, (round(x1+switch_height/2+1), round((y1+y2)/2-switch_height/2)), (round(x1+switch_width-switch_height/2-1), round((y1+y2)/2+switch_height/2)), switch_color, -1, cv2.LINE_AA)
            if animation_state < 1:
                cv2.circle(variables.FRAME, (round(x1+switch_height/2+(switch_width-switch_height)*(1-animation_state)), round((y1+y2)/2)), round(switch_height/2.5), switch_knob_color, -1, cv2.LINE_AA)
            else:
                cv2.circle(variables.FRAME, (round(x1+switch_height/2), round((y1+y2)/2)), round(switch_height/2.5), switch_knob_color, -1, cv2.LINE_AA)
    text, fontscale, thickness, width, height = GetTextSize(text, round((x2-x1)), fontsize)
    cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, text_color, thickness, cv2.LINE_AA)
    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 and left_clicked == False and last_left_clicked == True:
        if setting is not None:
            variables.SWITCHES[text] = not state, current_time
            settings.Set(str(setting[0]), str(setting[1]), not state)
        return True, switch_hovered
    else:
        return False, switch_hovered