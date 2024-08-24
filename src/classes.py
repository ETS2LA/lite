class Button:
    text: str
    x1: int
    y1: int
    x2: int
    y2: int
    textColor: tuple
    fontSize: int
    round_corners: int
    buttonColor: tuple
    buttonHoverColor: tuple
    buttonSelectedColor: tuple
    buttonSelectedHoverColor: tuple
    buttonSelected: bool

    def  __init__(self, text, x1, y1, x2, y2, textColor, fontSize, round_corners=10, buttonColor=(47, 47, 47), buttonHoverColor=(67, 67, 67), buttonSelectedColor=(67, 67, 67), buttonSelectedHoverColor=(67, 67, 67), buttonSelected=False):
        self.text = text
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.textColor = textColor
        self.fontSize = fontSize
        self.round_corners = round_corners
        self.buttonColor = buttonColor
        self.buttonHoverColor = buttonHoverColor
        self.buttonSelectedColor = buttonSelectedColor
        self.buttonSelectedHoverColor = buttonSelectedHoverColor
        self.buttonSelected = buttonSelected

    def draw(self, frame):
        ...

    def get_state(self):
        # Get the click and hover state based on the coordinates, then return them
        ...
        
class Label:
    text: str
    x1: int
    y1: int
    x2: int
    y2: int
    textColor: tuple
    fontSize: int
    
    def __init__(self, text, x1, y1, x2, y2, textColor, fontSize):
        self.text = text
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.textColor = textColor
        self.fontSize = fontSize
        
    def draw(self, frame):
        # Draw the label on the frame using the data
        ...
        