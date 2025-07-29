from pygame import Vector2
from pygame.rect import Rect
from pygame.color import Color

class Platform():
    def __init__(self, rect:Rect, color:Color, motion = Vector2(0)):
        self.rect = rect
        self.color = color
        self.motion = motion