from src.classes import Button, Label
import src.variables as variables
from typing import cast
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


def DrawLabel(label: Label):
    global frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    
    # Same thing as what I explained with the DrawButton one
    x1 = label.x1
    y1 = label.y1
    x2 = label.x2
    y2 = label.y2
    text = label.text
    fontsize = label.fontSize
    textcolor = label.textColor
    
    text, fontscale, thickness, width, height = GetTextSize(text, round((x2-x1)), fontsize)
    cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, textcolor, thickness, cv2.LINE_AA)


def DrawButton(button: Button):
    global frame_width, frame_height, mouse_x, mouse_y, left_clicked, right_clicked, last_left_clicked, last_right_clicked
    
    if button.x1 <= mouse_x * frame_width <= button.x2 and button.y1 <= mouse_y * frame_height <= button.y2:
        buttonhovered = True
    else:
        buttonhovered = False
        
    # I didn't feel like rewriting them all so I just assign them here.
    # eventually it might be beneficial to move all this over to the button class itself and then just call the draw method like
    # button.draw(variables.FRAME)
    x1 = button.x1
    y1 = button.y1
    x2 = button.x2
    y2 = button.y2
    round_corners = button.round_corners
    buttoncolor = button.buttonColor
    buttonhovercolor = button.buttonHoverColor
    buttonselectedcolor = button.buttonSelectedColor
    buttonselectedhovercolor = button.buttonSelectedColor
    text = button.text
    fontsize = button.fontSize
    textcolor = button.textColor
        
    if button.buttonSelected == True:
        if buttonhovered == True:
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), 
                                           (round(x2-round_corners/2), round(y2-round_corners/2)), 
                                           buttonselectedhovercolor, 
                                           round_corners, 
                                           cv2.LINE_AA)
            
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), 
                                           (round(x2-round_corners/2), round(y2-round_corners/2)), 
                                           buttonselectedhovercolor, 
                                           -1, 
                                           cv2.LINE_AA)
        else:
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), 
                                           (round(x2-round_corners/2), round(y2-round_corners/2)), 
                                           buttonselectedcolor, 
                                           round_corners, 
                                           cv2.LINE_AA)
            
            cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), 
                                           (round(x2-round_corners/2), round(y2-round_corners/2)), 
                                           buttonselectedcolor, 
                                           -1, 
                                           cv2.LINE_AA)
    elif buttonhovered == True:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), 
                                       (round(x2-round_corners/2), round(y2-round_corners/2)), 
                                       buttonhovercolor, 
                                       round_corners, 
                                       cv2.LINE_AA)
        
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), 
                                       (round(x2-round_corners/2), round(y2-round_corners/2)), 
                                       buttonhovercolor, 
                                       -1, 
                                       cv2.LINE_AA)
    else:
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), 
                                       (round(x2-round_corners/2), round(y2-round_corners/2)), 
                                       buttoncolor, 
                                       round_corners, 
                                       cv2.LINE_AA)
        
        cv2.rectangle(variables.FRAME, (round(x1+round_corners/2), round(y1+round_corners/2)), 
                                       (round(x2-round_corners/2), round(y2-round_corners/2)), 
                                       buttoncolor, 
                                       -1, 
                                       cv2.LINE_AA)
        
    text, fontscale, thickness, width, height = GetTextSize(text, round((x2-x1)), fontsize)
    cv2.putText(variables.FRAME, text, (round(x1 + (x2-x1) / 2 - width / 2), round(y1 + (y2-y1) / 2 + height / 2)), cv2.FONT_HERSHEY_SIMPLEX, fontscale, textcolor, thickness, cv2.LINE_AA)
    if x1 <= mouse_x * frame_width <= x2 and y1 <= mouse_y * frame_height <= y2 and left_clicked == False and last_left_clicked == True:
        return True, buttonhovered
    else:
        return False, buttonhovered