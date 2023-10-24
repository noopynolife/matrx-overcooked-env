# -*- coding: utf-8 -*-
"""
Created on Mon Jun 12 14:17:47 2023

@author: cornelissennaj
"""

from .recipes import Recipe, Simple


class Plate(Recipe):
    def __init__(self):
        super().__init__([Simple("plate")], [], [])

class Ingredient(Recipe):
    def __init__(self, ingredient, is_base=False):
        if is_base:
            super().__init__([], [Simple(ingredient)], [])
        else:
            super().__init__([], [], [Simple(ingredient)])
        
class Tomato(Ingredient):
    def __init__(self):
        super().__init__("tomato")
        
class Onion(Ingredient):
    def __init__(self):
        super().__init__("onion")
        
class Lettuce(Ingredient):
    def __init__(self):
        super().__init__("lettuce")