# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 17:51:31 2023

@author: cornelissennaj
"""

import os
from PIL import Image

def percent2target(target, box):
    w, h = int(box[0]*target[0]), int(box[1]*target[1])
    wx, hx = int(box[2]*target[0]), int(box[3]*target[1])
    return w, h, wx, hx

def center_2d_box(box):
    if len(box) == 2:
        box = (box[0], box[1], 1.0, 1.0)
        if box[0] < 0.5:
            box = (box[0], box[1], 1-box[0], box[3])
        if box[1] < 0.5:
            box = (box[0], box[1], box[2], 1-box[1])
    return box
    
def overlay_image(overlay, base, target_size=(180,180), box=(0, 0, 1.0, 1.0)):
    assert not (overlay is None and base is None)
    if base is None:
        return overlay
    if overlay is None:
        return base
    
    # Make sure that if we cannot find an image we use the 'not found' image
    media_folder = os.path.join(os.path.realpath("overcooked_env"), "images")
    if not os.path.exists(media_folder+"\\"+overlay):
        overlay = "not_found.png"
    if not os.path.exists(media_folder+"\\"+base):
        # Always overlay 'not found' on top if we do a straight overlay
        if box == (0, 0, 1.0, 1.0):
            base = overlay
            overlay = "not_found.png"
        else:
            base = "not_found.png"

    # Do not make excessive copies (could add box == (0, 0, 1.0, 1.0))
    if base.endswith(overlay):
        return base
    
    filename = "temp\\"+base.split(".png")[0].replace("\\", '_').replace("temp_", "")
    filename = filename+"_"+overlay.split(".png")[0].replace("\\", '_').replace("temp_", "")+".png"
    if not os.path.exists(media_folder+"\\"+filename):

        # open the empty table image and the specified image
        base_image = Image.open(media_folder+"\\"+base).convert("RGBA")
        base_image = base_image.resize(target_size)
        overlay_image = Image.open(media_folder+"\\"+overlay).convert("RGBA")
    
        # Work out some sizing
        box = center_2d_box(box)
        real_box = percent2target(target_size, box)
        inner_box = real_box[2]-real_box[0], real_box[3]-real_box[1]
        overlay_image = overlay_image.resize(inner_box)

        # overlay the specified image onto the table, save in temp folder
        base_image.paste(overlay_image, box=real_box, mask=overlay_image)
        base_image.save(media_folder+"\\"+filename)
        
        base_image.close()
        overlay_image.close()
            
    # set the temp file as img source
    return filename

class Direction():
        
    def from_name(name):
        if name == Direction.North.name:
            return Direction.North()
        if name is Direction.East.name:
            return Direction.East()
        if name is Direction.South.name:
            return Direction.South()
        if name is Direction.West.name:
            return Direction.West()
        
    def inverse(direction):
        if direction.name == Direction.North.name:
            return Direction.South()
        if direction.name == Direction.East.name:
            return Direction.West()
        if direction.name == Direction.South.name:
            return Direction.North()
        if direction.name == Direction.West.name:
            return Direction.East()        
    
    def clockwise(direction):
        if direction.name == Direction.North.name:
            return Direction.East()
        if direction.name == Direction.East.name:
            return Direction.South()
        if direction.name == Direction.South.name:
            return Direction.West()
        if direction.name == Direction.West.name:
            return Direction.North()
        
    def counterwise(direction):
        if direction.name == Direction.North.name:
            return Direction.West()
        if direction.name == Direction.East.name:
            return Direction.North()
        if direction.name == Direction.South.name:
            return Direction.East()
        if direction.name == Direction.West.name:
            return Direction.South()
        
    class _GridDirection():

        def __init__(self, dx=0, dy=0, img_append=None):
            self.dx = dx
            self.dy = dy
            self.img_append = img_append
        
        def get_dx_dy(self):
            return self.dx, self.dy            
    
        def directional_img(self, path):
            if self.img_append is None:
                return path
        
            for p in Direction.direction_paths:
                path = path.replace('_'+p, "")
                
            prep, delimiter, app = path.rpartition('.')
            return prep + '_' + self.img_append+delimiter+app
        
    class North(_GridDirection):
        name = 'north'
        def __init__(self):
            super().__init__(dx=0, dy=-1, img_append=self.name)

    class East(_GridDirection):
        name = 'east'
        def __init__(self):
            super().__init__(dx=1, dy=0, img_append=self.name)

    class South(_GridDirection):
        name = 'south'
        def __init__(self):
            super().__init__(dx=0, dy=1, img_append=self.name)
            
    class West(_GridDirection):
        name = 'west'
        def __init__(self):
            super().__init__(dx=-1, dy=0, img_append=self.name)
            
    direction_paths = [North.name, East.name, South.name, West.name]