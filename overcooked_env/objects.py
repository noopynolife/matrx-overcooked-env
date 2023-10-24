# -*- coding: utf-8 -*-
"""
Created on Tue May 30 17:01:33 2023

@author: cornelissennaj
"""

from matrx.objects import EnvObject
import json

from .util import overlay_image
from .recipes import Recipe
from .tasks import Task
from .predicates import PredQuality, Merged, Simple

from random import Random

class TableTop(EnvObject):
    
    BASE_IMG = "environment\\tabletop.png"
    DISPLAY_NAME = "Middle Counter"
    SEARCH_NAME = "empty_counter_table"

    def __init__(self, location, name=SEARCH_NAME, 
                 class_callable=None, 
                 img_name=BASE_IMG,
                 is_traversable=False, 
                 is_movable=False,
                 is_usable=False,
                 is_counter=True,
                 **kwargs):

        if class_callable is None:
            class_callable = TableTop
        
        super().__init__(location=location, 
                         name=name,
                         class_callable=class_callable,
                         is_traversable=is_traversable,
                         is_movable=is_movable,
                         is_usable=is_usable,
                         img_name = img_name,
                         is_counter = is_counter,
                         visualization_layer = 66,
                         search_name = self.SEARCH_NAME,
                         display_name = self.DISPLAY_NAME,
                         **kwargs)

    def get_as_task(self, task_type):
        return Task(task_type, unique_name=self.SEARCH_NAME, display_name=self.DISPLAY_NAME, resource_name=self.custom_properties['img_name'])

class CuttingBoard(TableTop):
    
    TOOL_IMG = "tools\\cutboard.png"
    RECIPES = dict()
    DISPLAY_NAME = "Cutting Board"
    SEARCH_NAME = "cutting_chopping_board"

    def __init__(self, location, name=SEARCH_NAME, 
                 img_name=TOOL_IMG, 
                 is_traversable=False, 
                 is_movable=False,
                 is_usable=True,
                 use_type=None,
                 **kwargs):
    
        self.use_type = use_type
        img_name = overlay_image(self.TOOL_IMG, base=self.BASE_IMG)
        
        super().__init__(location=location, 
                         name=name,
                         class_callable=CuttingBoard,
                         is_traversable=is_traversable,
                         is_movable=is_movable,
                         is_usable=is_usable,
                         img_name=img_name,
                         is_counter=False,
                         use_type=self.use_type,
                         recipes = self.RECIPES, 
                         **kwargs)
    
    def can_use(self, **kwargs):
        itemStacks = kwargs['itemstacks']
        
        for itemStack in itemStacks:
            key = json.dumps(itemStack.stack.get_unmarked())

            if key in self.RECIPES:
                return True
        return False
                
    def use(self, **kwargs):
        itemStacks = kwargs['itemstacks']
        agent = kwargs['use_agent']
        
        for itemStack in itemStacks:
            key = json.dumps(itemStack.stack.get_unmarked())

            if key in self.RECIPES:
                new_recipe = Recipe.from_str_gen(self.RECIPES[key])
                new_recipe = _flawed_recipe(new_recipe, agent, self.use_type)
                itemStack.update_stack(new_recipe)
                            
class SourceTop(TableTop):
        
    BASE_IMG = "environment\\source.png"
    DISPLAY_NAME = "Source"
    SEARCH_NAME = "source_box"
    
    def __init__(self, location, name=SEARCH_NAME, 
                 is_traversable=False, 
                 is_movable=False,
                 source_stack=None,
                 **kwargs):
        
        assert source_stack is not None, "Source object must have a source_stack"
        self.stack = source_stack
        img_name = overlay_image(self.stack.get_img(), base=self.BASE_IMG, box=(0.20, 0.20))

        if name == SourceTop.SEARCH_NAME:
            total = self.stack.serve_base + self.stack.base_ingredients + self.stack.toppings
            name += str(total[0])
            self.DISPLAY_NAME = self.stack.get_display_name + " " + self.DISPLAY_NAME
            self.SEARCH_NAME = self.stack.get_unique_name + "_" + self.SEARCH_NAME

        super().__init__(location=location, 
                         name=name,
                         class_callable=SourceTop,
                         is_traversable=is_traversable,
                         is_movable=is_movable,
                         img_name = img_name,
                         stack=self.stack,
                         is_source=True,
                         is_counter=False,
                         **kwargs)
    
    def new_stack(self, location, agent):
        new_stk = self.stack.copy()
        new_stk = _flawed_recipe(new_stk, agent, Simple.name)
        return ItemStack(location, stack=new_stk)
    
class TrashTop(TableTop):
        
    BASE_IMG = "environment\\trash.png"
    DISPLAY_NAME = "Trash"
    SEARCH_NAME = "trash_bin"
    
    def __init__(self, location, name=SEARCH_NAME, 
                 is_traversable=False, 
                 is_movable=False,
                 **kwargs):

        super().__init__(location=location, 
                         name=name,
                         class_callable=TrashTop,
                         is_traversable=is_traversable,
                         is_movable=is_movable,
                         img_name = self.BASE_IMG,
                         stack=[],
                         is_counter=False,
                         is_trash=True,
                         **kwargs)

class DeliveryTop(TableTop):
     BASE_IMG = "environment\\delivery.png"
     DISPLAY_NAME = "Delivery"
     SEARCH_NAME = "delivery_table"

     RECIPES = set()
     SCORE = 0
     GOALS = []
     DELIVERED = []
     REDO = []
     FAILED = []
     ENDTICK = 0
     
     WELCOME = ""
     GOODBYE = ""
     
     def __init__(self, location, name=SEARCH_NAME, 
             is_traversable=False, 
             is_movable=False,
             **kwargs): 
                          
        super().__init__(location=location, 
                      name=name,
                      class_callable=DeliveryTop,
                      is_traversable=is_traversable,
                      is_movable=is_movable,
                      img_name = self.BASE_IMG,
                      is_delivery=True,
                      is_counter=False,
                      goals=self.GOALS,
                      redo=self.REDO,
                      failed=self.FAILED,
                      endtick=self.ENDTICK,
                      delivered=self.DELIVERED,
                      welcome_message=self.WELCOME,
                      goodbye_message=self.GOODBYE,
                      simulation_completed=False,
                      **kwargs)
         
     def deliver_stack(self, itemStack, currentTick):
        
        clean = itemStack.stack.get_unmarked().get_good_quality()
        key = json.dumps(clean)
        
        recipe_goals = [x for x in self.GOALS if not x['is_done']]
        
        if key in self.RECIPES:
            stack = itemStack.stack
            itemStack.stack = []
            
            for i in range(len(recipe_goals)):
                if (recipe_goals[i]['appears_at'] <= currentTick) and (recipe_goals[i]['max_nr_ticks'] >= currentTick) and Recipe.from_json_gen(recipe_goals[i]['target']).get_unmarked().get_good_quality() == clean:
                    success = False
                    if stack.is_quality_good():
                        completed = recipe_goals.pop(i)
                        self.DELIVERED.append(completed)
                        self.SCORE += completed['max_reward']
                        print("Successfull delivery! Team score increased to "+str(self.SCORE) + " points.")
                        success = True
                    else:
                        if not recipe_goals[i]['redo']:
                            self.REDO.append(recipe_goals[i])
                        else:
                            self.FAILED.append(recipe_goals[i])
                        print("Delivery quality was not up to par.. Team is awarded no points.")
                        
                    return True
            print("Incorrect delivery.. Team is awarded no points.")
        else:
            print("Incomplete dish, cannot be delivered")
        return False

class ItemStack(EnvObject):
    
    RECIPES = set()
    def prepend_recipes(self, RECIPES, prepend):
        RECIPES_copy = json.loads(json.dumps(RECIPES))
    
        for val in RECIPES.values():
            prep_val = json.dumps(prepend+json.loads(val))
            RECIPES_copy[prep_val] = prep_val
            
        for key in RECIPES.keys():
            prep_key = json.dumps(prepend+json.loads(key))
            RECIPES_copy[prep_key] = prep_key
            
        return RECIPES_copy
    
    def __init__(self, location, name=None, stack=None, img_name=None, **kwargs):                
        assert stack is not None, "ItemStack objects should not have an empty recipe on creation"
        self.stack = stack

        img_name = self.stack.get_img()
        
        if name is None:
            name = "itemstack_"+str(len(self.stack))
                   
        super().__init__(location=location, 
                         name=name,
                         class_callable=ItemStack,
                         is_traversable=True,
                         is_movable=True,
                         stack=self.stack,
                         img_name = img_name,
                         visualization_layer = 99,
                         **kwargs)
           
    def update_stack(self, new_stack):
        self.stack = new_stack
        self.custom_properties['stack'] = self.stack
        self.custom_properties['img_name'] = self.stack.get_img()
        
    def merge_stack(self, itemStack, agent):
        hold = itemStack.stack
        new_stack = self.stack + hold
        
        key = json.dumps(new_stack.get_good_quality()) #quality does not matter for the merge
        
        if key in self.RECIPES:
            new_stack = _flawed_recipe(new_stack, agent, Merged.name)
            self.update_stack(new_stack)
            itemStack.stack = []
            return True
        else:
            return False
        
class ProgressBar(EnvObject):
    def __init__(self, location, stages, name="Bar", **kwargs):   

        self.stages = stages;
        self.current = 0;
             
        super().__init__(location=location, 
                 name=name,
                 class_callable=ProgressBar,
                 is_traversable=True,
                 is_progress=True,
                 almost_done=len(self.stages)-1 == self.current+1,
                 is_done=len(self.stages)-1 == self.current,
                 stages=self.stages,
                 img_name = "icons\\progress_"+str(self.stages[self.current])+".png",
                 visualization_layer = 145,
                 **kwargs)
    
    def next_stage(self):
        self.current += 1
        self.custom_properties['almost_done'] = len(self.stages) == self.current+1
        self.custom_properties['is_done'] = len(self.stages) == self.current
        if not self.custom_properties['is_done']:
            self.custom_properties['img_name'] =  "icons\\progress_"+str(self.stages[self.current])+".png"

def _flawed_recipe(recipe, agent, predType):
    for x in recipe.serve_base + recipe.base_ingredient + recipe.toppings:
        if predType == x.name and str(x) in agent.custom_properties['reliability']['liabilities']:
            liability = agent.custom_properties['reliability']['liabilities'][str(x)]
            rand = Random()
            rand.seed(liability['rand_seed'])
            _ = [rand.random() for x in range(liability['rand_tracker'])]
            liability['rand_tracker'] += 1
            next_ = rand.random()
            
            if liability['fault_rate'] > next_:    
                x.quality = liability['fault_type']
                
    return recipe