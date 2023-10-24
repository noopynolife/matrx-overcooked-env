# -*- coding: utf-8 -*-
"""
Created on Tue May 30 14:13:33 2023

@author: cornelissennaj
"""
from .actions import Use, TakeOrPut, TurnAndMove

WASD = {
    'w': TurnAndMove.North.__name__,
    'd': TurnAndMove.East.__name__,
    's': TurnAndMove.South.__name__,
    'a': TurnAndMove.West.__name__,
    'Enter': Use.__name__,
    ' ': TakeOrPut.__name__,
    
}

IJKL = {
    'i': TurnAndMove.North.__name__,
    'l': TurnAndMove.East.__name__,
    'k': TurnAndMove.South.__name__,
    'j': TurnAndMove.West.__name__,
}

ARROWS = {
    'ArrowUp': TurnAndMove.North.__name__,
    'ArrowRight': TurnAndMove.East.__name__,
    'ArrowDown': TurnAndMove.South.__name__,
    'ArrowLeft': TurnAndMove.West.__name__,
}
