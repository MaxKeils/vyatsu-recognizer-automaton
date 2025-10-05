from enum import Enum

class HintLevel(int, Enum):
    NO_HINTS = 1
    LIGHT_HINTS = 2
    FULL_HINTS = 3