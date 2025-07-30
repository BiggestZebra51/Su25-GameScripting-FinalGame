from pygame.rect import Rect
from pygame import Surface

class ScoreStat():
    def __init__(self, text:Surface, rect:Rect):
        self.value:int|float = 0
        self.text = text
        self.rect = rect