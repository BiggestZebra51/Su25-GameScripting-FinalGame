from pygame import Vector2
from pygame.rect import Rect
from pygame.color import Color

class Platform():
    def __init__(self, sprite_index:int, rect:Rect, motion = Vector2(0)):
        self.sprite_index = sprite_index
        self.rect = rect
        self.motion = motion