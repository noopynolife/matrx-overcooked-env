# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 16:00:15 2023

@author: cornelissennaj
"""
from enum import Enum

"""
Simple Enum to keep track of different ingredient qualities
"""
class PredQuality(str, Enum):
    GOOD = ""
    POOR = "poorly"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        if isinstance(other, PredQuality):
            return self.value == other.value
        else:
            return False
    
    def __hash__(self):
        return hash(self.value)

# PREDICATES
# --------------------------------------------------------------
class Predicate(dict):
    def __init__(self, name, args, quality=PredQuality.GOOD, basic=False):
        self.name = name
        if basic or isinstance(args, tuple):
            self.args = args
        elif isinstance(args, list):
            self.args = tuple(x for x in args)
        else:
            self.args = (args,)
        self.quality = quality
        self.init_dict()

    def init_dict(self):
        super().__init__(name=self.name, 
                 args=self.args,
                 quality=self.quality)

    def __eq__(self, other):
        return (self.name == other.name) and (self.args == other.args)
    
    def __lt__(self, other):
        if self.name == other.name:
            return self.args < other.args
        else:
            return self.name < other.name
        
    def __gt__(self, other):
        if self.name == other.name:
            return self.args > other.args
        else:
            return self.name > other.name    
        
    def __hash__(self):
        return hash((self.name, self.args))

    def __str__(self):
        return '{}({})'.format(self.name, ', '.join(str(x) for x in self.args))

    def deepcopy(self):
        return type(self)(self.args, self.quality)    
        
    def is_quality_good(self):
        if self.quality != PredQuality.GOOD:
            return False
        
        for x in self.args:
            if not x.is_quality_good():
                return False
        return True

    def set_quality_good(self, recursive=True):
        self.quality = PredQuality.GOOD
        if recursive: 
            for x in self.args: x.set_quality_good()
        self.init_dict()

    def get_base_preds(self):
        return [x.get_base_preds() for x in self.args]
    
    def get_display_name(self):
        return '{} {}'.format(self.name.capitalize(), ('_'.join(x.get_display_name() for x in self.args)))
    
    def get_resource_name(self):
        prepend = ""
        if self.quality != "":
            prepend = self.quality+"_" 
        return '{}{}({})'.format(prepend, self.name, ('_'.join(x.get_resource_name() for x in self.args))).lower()
    
    def from_string(ing_str):
        # see if we are dealing with a generated json or a user created json
        if isinstance(ing_str, dict):
            return Predicate.from_json_gen(ing_str)
            
        if not '(' in ing_str:
            return Simple(ing_str)
        
        pred, _, ing = ing_str.partition('(')
        ing, _, _ = ing.rpartition(')')
        
        assert pred in PREDICATE_MAP, "Unknown predicate type" + pred

        return PREDICATE_MAP[pred](Predicate.from_string(ing))
    
    def from_json_gen(ing_json):      
        pred = ing_json['name']
        args = ing_json['args']
        
        #quality = ing_json['quality']
        
        if isinstance(args, str):
            return PREDICATE_MAP[pred](args)
        else:
            return PREDICATE_MAP[pred](Predicate.from_json_gen(args[0]))
        

class Simple(Predicate):
    name = 'Simple'
    def __init__(self, obj=None, quality=PredQuality.GOOD):
        super().__init__(self.name, obj, quality=quality, basic=True)
    def __str__(self):
        return self.args
    def is_quality_good(self):
        return self.quality == PredQuality.GOOD
    def set_quality_good(self):
        self.quality = PredQuality.GOOD
        self.init_dict()
    def get_resource_name(self):
        prepend = ""
        if self.quality != "":
            prepend = self.quality+"_" 
        return (prepend+str(self)).lower()
    def get_base_preds(self):
        return self
    def get_display_name(self):
        return str(self).capitalize()    
    def deepcopy(self):
        return Simple(self.args, self.quality)   
class Merged(Predicate):
    name = 'Merged'
    def __init__(self, obj):
        assert False, "Merge predicate should not be used in json config"
class Deliverable(Predicate):
    name = 'Deliverable'
    def __init__(self, obj):
        assert False, "Deliverable predicate should not be used in json config"
class Family(Predicate):
    name = 'Family'
    def __init__(self, obj, quality=PredQuality.GOOD):
        super().__init__(self.name, obj, quality=quality)
class Chopped(Predicate):
    name = 'Chopped'
    def __init__(self, obj, quality=PredQuality.GOOD):
        super().__init__(self.name, obj, quality=quality)
class Cooked(Predicate):
    name = 'Cooked'
    def __init__(self, obj, quality=PredQuality.GOOD):
        super().__init__(self.name, obj, quality=quality)
class Grilled(Predicate):
    name = 'Grilled'
    def __init__(self, obj, quality=PredQuality.GOOD):
        super().__init__(self.name, obj, quality=quality)
        
PREDICATE_MAP = {Simple.name : Simple,
                 Merged.name : Merged,
                 Chopped.name : Chopped,
                 Cooked.name : Cooked,
                 Grilled.name : Grilled,
                 Family.name : Family}