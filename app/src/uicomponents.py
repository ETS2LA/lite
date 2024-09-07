import src.translate as translate
import src.variables as variables
import src.settings as settings
import threading
import pynput
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

scroll_event_queue = []
def handle_scroll_events():
    global scroll_event_queue
    with pynput.mouse.Events() as events:
        while variables.BREAK == False:
            event = events.get()
            if isinstance(event, pynput.mouse.Events.Scroll):
                scroll_event_queue.append(event)
scroll_event_thread = threading.Thread(target=handle_scroll_events, daemon=True).start()


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
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked, scroll_event_queue
    y1 += variables.TITLE_BAR_HEIGHT
    y2 += variables.TITLE_BAR_HEIGHT
    texts = text.split("\n")
    line_height = ((y2-y1) / len(texts))
    for i, t in enumerate(texts):
        t = translate.Translate(t)
        text, fontscale, thickness, width, height = GetTextSize(t, round((x2-x1)), line_height / 1.5 if line_height / 1.5 < fontsize else fontsize)
        cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (i + 0.5) * line_height + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, text_color, thickness, cv2.LINE_AA)


def Button(text="NONE", x1=0, y1=0, x2=100, y2=100, fontsize=variables.FONT_SIZE, round_corners=5, button_selected=False, text_color=variables.TEXT_COLOR, button_color=variables.BUTTON_COLOR, button_hover_color=variables.BUTTON_HOVER_COLOR, button_selected_color=variables.BUTTON_SELECTED_COLOR, button_selected_hover_color=variables.BUTTON_SELECTED_HOVER_COLOR):
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked, scroll_event_queue
    y1 += variables.TITLE_BAR_HEIGHT
    y2 += variables.TITLE_BAR_HEIGHT
    text = translate.Translate(text)
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
        return True, left_clicked and button_hovered, button_hovered
    else:
        return False, left_clicked and button_hovered, button_hovered


def Switch(text="NONE", x1=0, y1=0, x2=100, y2=100, switch_width=40, switch_height=20, text_padding=10, state=False, setting=None, fontsize=variables.FONT_SIZE, text_color=variables.TEXT_COLOR, switch_color=variables.SWITCH_COLOR, switch_knob_color=variables.SWITCH_KNOB_COLOR, switch_hover_color=variables.SWITCH_HOVER_COLOR, switch_enabled_color=variables.SWITCH_ENABLED_COLOR, switch_enabled_hover_color=variables.SWITCH_ENABLED_HOVER_COLOR):
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked, scroll_event_queue
    current_time = time.time()
    y1 += variables.TITLE_BAR_HEIGHT
    y2 += variables.TITLE_BAR_HEIGHT
    text = translate.Translate(text)
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
    cv2.putText(variables.FRAME, text, (round(x1 + switch_width + text_padding), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, text_color, thickness, cv2.LINE_AA)
    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 and left_clicked == False and last_left_clicked == True:
        if setting is not None:
            variables.SWITCHES[text] = not state, current_time
            settings.Set(str(setting[0]), str(setting[1]), not state)
        return True, left_clicked and switch_hovered, switch_hovered
    else:
        return True, left_clicked and switch_hovered, switch_hovered


def Dropdown(text="NONE", items=["NONE"], default_item=0, x1=0, y1=0, x2=100, y2=100, dropdown_height=100, dropdown_padding=5, round_corners=5, fontsize=variables.FONT_SIZE, text_color=variables.TEXT_COLOR, dropdown_color=variables.BUTTON_COLOR, dropdown_hover_color=variables.BUTTON_HOVER_COLOR):
    global foreground_window, frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked, scroll_event_queue
    y1 += variables.TITLE_BAR_HEIGHT
    y2 += variables.TITLE_BAR_HEIGHT
    if text not in variables.DROPDOWNS:
        default_item = int(max(min(default_item, len(items) - 1), 0))
        variables.DROPDOWNS[text] = False, settings.Get("DropdownSelections", str(text), default_item)

    dropdown_selected, selected_item = variables.DROPDOWNS[text]

    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 + ((dropdown_height + dropdown_padding) if dropdown_selected else 0) and foreground_window and (variables.CONTEXT_MENU[0] == False or text in str(variables.CONTEXT_MENU_ITEMS)):
        dropdown_hovered = True
        dropdown_pressed = left_clicked
        dropdown_changed = True if last_left_clicked == True and left_clicked == False and dropdown_selected == True else False
        dropdown_selected = not dropdown_selected if last_left_clicked == True and left_clicked == False else dropdown_selected
    else:
        dropdown_hovered = False
        dropdown_pressed = False
        dropdown_changed =  dropdown_selected
        dropdown_selected = False

    if dropdown_hovered == True:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), dropdown_hover_color, round_corners, cv2.LINE_AA)
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), dropdown_hover_color, -1, cv2.LINE_AA)
    else:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), dropdown_color, round_corners, cv2.LINE_AA)
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), (round(x2-round_corners/2), round(y2-round_corners/2)), dropdown_color, -1, cv2.LINE_AA)
    if dropdown_selected == True:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y2+dropdown_padding+round_corners/2)), (round(x2-round_corners/2), round(y2+dropdown_height+dropdown_padding-round_corners/2)), dropdown_hover_color, round_corners, cv2.LINE_AA)
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y2+dropdown_padding+round_corners/2)), (round(x2-round_corners/2), round(y2+dropdown_height+dropdown_padding-round_corners/2)), dropdown_hover_color, -1, cv2.LINE_AA)

        _, _, thickness, _, _ = GetTextSize()
        padding = (y2 + y1) / 2 - variables.FONT_SIZE / 4 - y1
        height = round(y2 - padding) - round(y1 + padding)
        cv2.line(variables.FRAME, (round(x2 - padding - height), round(y1 + padding)), (round(x2 - padding), round(y2 - padding)), text_color, thickness, cv2.LINE_AA)
        cv2.line(variables.FRAME, (round(x2 - padding - height), round(y1 + padding)), (round(x2 - padding  - height * 2), round(y2 - padding)), text_color, thickness, cv2.LINE_AA)

        while scroll_event_queue:
            event = scroll_event_queue.pop(0)
            if event.dy > 0:
                selected_item = (selected_item - 1) if selected_item > 0 else 0
            elif event.dy < 0:
                selected_item = (selected_item + 1) if selected_item < len(items) - 1 else len(items) - 1

        for i in range(3):
            line_height = (dropdown_height / 3)
            index = selected_item - 1 + i
            if index >= len(items):
                index = -1
            if index < 0:
                index = -1
            if index == -1:
                item = ""
            else:
                item = translate.Translate(items[index])
            if i == 1:
                item_text = "> " + item + " <"
            else:
                item_text = item
            item_text, fontscale, thickness, width, height = GetTextSize(item_text, round((x2-x1)), line_height / 1.5 if line_height / 1.5 < fontsize else fontsize)
            cv2.putText(variables.FRAME, item_text, (round(x1 + (x2-x1) / 2 - width / 2), round(y2 + dropdown_padding + (i + 0.5) * line_height + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, text_color, thickness, cv2.LINE_AA)

    else:

        _, _, thickness, _, _ = GetTextSize()
        padding = (y2 + y1) / 2 - variables.FONT_SIZE / 4 - y1
        height = round(y2 - padding) - round(y1 + padding)
        cv2.line(variables.FRAME, (round(x2 - padding - height), round(y2 - padding)), (round(x2 - padding), round(y1 + padding)), text_color, thickness, cv2.LINE_AA)
        cv2.line(variables.FRAME, (round(x2 - padding - height), round(y2 - padding)), (round(x2 - padding  - height * 2), round(y1 + padding)), text_color, thickness, cv2.LINE_AA)

        scroll_event_queue = []

    text_translated = translate.Translate(text)
    text_translated, fontscale, thickness, width, height = GetTextSize(text_translated, round((x2-x1)), fontsize)
    cv2.putText(variables.FRAME, text_translated, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, text_color, thickness, cv2.LINE_AA)

    variables.DROPDOWNS[text] = dropdown_selected, selected_item
    if dropdown_changed:
        settings.Set("DropdownSelections", str(text), int(selected_item))
    if dropdown_selected:
        variables.RENDER_FRAME = True

    return dropdown_changed, dropdown_pressed, dropdown_hovered