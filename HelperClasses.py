from pygame import Vector2
from pygame.rect import Rect
from pygame import Surface

class Platform():
    def __init__(self, sprite_index:int, rect:Rect, motion = Vector2(0)):
        self.sprite_index = sprite_index
        self.rect = rect
        self.motion = motion

class ScoreStat():
    def __init__(self, text:Surface, rect:Rect, multiplier:float = 1, real_time:bool = True):
        """
            `text` is the rendered label to display on the results page
            
            `rect` is the location to display

            `multiplier` if set scales this `value` in the score results, defaults to 1.0

            `real_time` if set controls whether value is used in level threshold, defaults to True
        """
        self.value:int|float = 0
        self.multiplier = multiplier
        self.real_time = real_time
        self.text = text
        self.rect = rect