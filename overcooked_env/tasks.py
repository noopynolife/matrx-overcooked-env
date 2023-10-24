# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 22:03:06 2023

@author: cornelissennaj
"""
from matrx.goals.goals import LimitedTimeGoal

from enum import Enum
import json
from .recipes import Recipe

"""
Simple Enum to keep track of different task types and make string comparisons
"""
class TaskType(str, Enum):
    MOVE = "move"
    GET = "get"
    USE = "use"
    CANCEL = "cancel"
    PLAY = "play"
    GOAL = "goal"
    PRIORITY = "priority"
    SERVE = "serve"
    MAKE_AND_SERVE = "make and serve"
    PREPARE = "prepare"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        if isinstance(other, TaskType):
            return self.value == other.value
        else:
            return False

"""
Simple Enum to keep track of different task types and make string comparisons
"""
class TaskId(str, Enum):
    CHOP = "chop_cut_knife_dice"
    
    PRIO_SPEED = "priority_speed_fast_goal"
    PRIO_SAFETY = "priority_workspace_safety_goal"
    PRIO_QUALITY = "priority_food_quality_goal"
    
    PLAY_VEG = "play_prepare_all_vegetables"
    PLAY_ASSEMBLE = "play_assemble_all_dishes"
    PLAY_SERVE = "play_serve_all_dishes"
    
    NONE = "none"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        if isinstance(other, TaskType):
            return self.value == other.value
        else:
            return False

"""
This object is supported by the HTML / Javascript interface and can be displayed as a button
"""
class Task(dict):
    
    def __init__(self, task_type, unique_name, display_name, resource_name, mark=None):
        
        self.task_type = task_type
        self.unique_name = unique_name
        self.display_name = display_name
        self.resource_name = resource_name
        self.mark = mark
        
        super().__init__(task_type=self.task_type,
                         unique_name=self.unique_name,
                         display_name=self.display_name,
                         resource_name=self.resource_name,
                         mark=self.mark)
        

class GoalBook(dict):
     def __init__(self, goals):
        self.goals = goals
        self.world_goal = TimedRestaurantGoal(self.goals[-1].max_nr_ticks, spare_ticks=self.goals[-1].expires_after*0.45)
        super().__init__(goals=self.goals,
                         world_goal=self.world_goal)

     def to_json_string(self):
        return json.dumps(self)

     def from_json_string(json_str):
        return GoalBook.from_json_object(json.loads(json_str))
    
     def from_json_object(json_obj):
        goals = []
        for i, g in enumerate(json_obj['goals']):
             goal = TimedRecipeGoal.from_json_object(g)
             goal['target'].set_mark("TimedDelivery_" + str(i) )
             goals.append(goal)
                                    
        return GoalBook(goals)
    
     def register_goals_to_world(self, world_builder, overwrite=False):
        if overwrite:
            world_builder.add_goal([], overwrite=True)
        world_builder.add_goal(self.goals)
        world_builder.add_goal([self.world_goal])
    
     def register_goals_to_tool(self, tool, overwrite=False):
        if overwrite:
            tool.SCORE = 0
            tool.GOALS.clear()
            tool.REDO.clear()
            tool.FAILED.clear()
            tool.DELIVERED.clear()
        tool.GOALS.extend(self.goals)
        tool.ENDTICK = self.world_goal.max_nr_ticks
             
class TimedRecipeGoal(dict, LimitedTimeGoal):
    def __init__(self, target, appears_at, expires_after, max_reward):
        self.target = target
        self.appears_at = appears_at
        self.expires_after = expires_after
        self.max_reward = max_reward
        self.max_nr_ticks=self.appears_at+self.expires_after
        self.is_done = False
        self.redo = False
        self.init_dict()
        
    def init_dict(self):
        super().__init__(max_nr_ticks=self.max_nr_ticks,
                         target=self.target,
                         appears_at=self.appears_at,
                         expires_after=self.expires_after,
                         max_reward=self.max_reward,
                         is_done=self.is_done,
                         redo=self.redo)
    
    def goal_reached(self, grid_world):
        if self.is_done == True:
            return self.is_done
        for obj in grid_world.environment_objects.values():
            if 'is_delivery' in obj.custom_properties and obj.custom_properties['is_delivery']:
                for goal in obj.DELIVERED:
                    if self['target']['mark'] == goal['target']['mark']:
                        self.is_done = True
                        self.init_dict()
                        print("RECIPE GOAL WITH MARK ", self['target']['mark'], " COMPLETED, ending at tick ", grid_world.current_nr_ticks)
                    
                if not self.redo:
                    for goal in obj.REDO:
                        if self['target']['mark'] == goal['target']['mark']: 
                            self.redo = True
                            set_back = self.expires_after * 0.2
                            self.appears_at = grid_world.current_nr_ticks - set_back # give the team fresh time for a redo
                            self.max_nr_ticks = grid_world.current_nr_ticks + (self.expires_after ) - set_back # the team is given less time for a redo
                            self.init_dict()
                            print("RECIPE GOAL WITH MARK ", self['target']['mark'], " MUST BE REDONE, ending at tick ", self.max_nr_ticks)
                
                else:
                    for goal in obj.FAILED:
                        if self['target']['mark'] == goal['target']['mark']: 
                            self.is_done = True
                            self.init_dict()
                            print("RECIPE GOAL WITH MARK ", self['target']['mark'], " FAILED, ending at tick ", grid_world.current_nr_ticks)
                
                if not self.is_done:
                    super().goal_reached(grid_world)
                    self.init_dict()    
                
                for i, goal in enumerate(obj.GOALS):
                    if self['target']['mark'] == goal['target']['mark']:
                        if not self.is_done:
                            obj.GOALS[i] = self # make sure these remain synced
                        else:
                            obj.GOALS.pop(i)

                return self.is_done   
        return self.is_done
    
    def from_json_object(json_obj):
        target = Recipe.from_json_gen(json_obj['target'])
        appears_at = json_obj['appears_at']
        expires_after = json_obj['expires_after']
        max_reward = json_obj['max_reward']
        return TimedRecipeGoal(target, appears_at, expires_after, max_reward)

    def __hash__(self):
        return hash(json.dumps(self))
    
class TimedRestaurantGoal(dict, LimitedTimeGoal):
    def __init__(self, max_nr_ticks, spare_ticks=500):
        self.max_nr_ticks = max_nr_ticks + spare_ticks
        self.spare_ticks = spare_ticks
        self.is_done = False
        self.init_dict()

    def init_dict(self):
          super().__init__(max_nr_ticks=self.max_nr_ticks,
                         spare_ticks=self.spare_ticks,
                         is_done=self.is_done)      
    
    def goal_reached(self, grid_world):
        currentTick = grid_world.current_nr_ticks
        if self.all_recipe_goals_completed(grid_world.simulation_goal, currentTick):
            if self.spare_ticks > 0:
                self.spare_ticks = 5 # we dont need our spare ticks here for possible faulty dishes
            self.complete(currentTick, grid_world)
        elif self.max_nr_ticks <= currentTick:
            self.complete(currentTick, grid_world)

        return self.is_done 
    
    def all_recipe_goals_completed(self, currentGoals, currentTick):
        recipe_goals = [x for x in currentGoals if 'target' in x]
        for goal in recipe_goals:
            if not goal.is_done:
                return False
        return True
    
    def complete(self, world_ticks, grid_world):
        if self.spare_ticks > 0:          
            self.max_nr_ticks = world_ticks + self.spare_ticks
            self.spare_ticks = 0
            self.init_dict()
            print("WORLD GOAL COMPLETED, ending at tick ", self.max_nr_ticks)
            for obj in grid_world.environment_objects.values():
                if 'is_delivery' in obj.custom_properties and obj.custom_properties['is_delivery']:
                    obj.custom_properties['simulation_completed'] = True
        elif self.max_nr_ticks <= world_ticks:
            self.is_done = True
            self.init_dict()
                
    def __hash__(self):
        return hash(json.dumps(self))