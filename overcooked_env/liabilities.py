# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 22:56:04 2023

@author: cornelissennaj
"""
import json
from random import Random

class Reliability(dict):
     def __init__(self, liabilities):
        self.liabilities = liabilities
        super().__init__(liabilities=self.liabilities)
    
     def to_json_string(self):
        return json.dumps(self)

     def from_json_string(json_str):
        return Reliability.from_json_object(json.loads(json_str))
    
     def from_json_object(json_obj):
        liabilities = dict()
        for lia in (json_obj['liabilities']):
            rand = Random()
            rand.seed("CookBOt")
            liabilities[lia['action']] = {"fault_type" : lia["fault_type"], # used to identify the correct image
                                          "fault_rate" : lia["fault_rate"],
                                          "rand_seed" : lia["rand_seed"],
                                          "rand_tracker" : 0} # how often % this fault occurs
            
        return Reliability(liabilities)