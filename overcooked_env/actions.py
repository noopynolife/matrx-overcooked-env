# -*- coding: utf-8 -*-
"""
Created on Thu Jun  1 16:29:43 2023

@author: cornelissennaj
"""

from matrx.actions.action import Action, ActionResult
from matrx.actions.move_actions import Move, MoveNorth, MoveSouth, MoveWest, MoveEast
from .util import overlay_image, Direction
from .objects import ProgressBar
import numpy as np

class PrintableActionResult(ActionResult):
    def __str__(self):
        out = self.result
        if isinstance(out, str):
            return out
        else:
            return str(out)

class Use(Action):
 
    class Result(PrintableActionResult):
        RESULT_SUCCESS = "An object was used succesfully."
        RESULT_PROGRESS = "Progress of a used object was increased succesfully."
        NO_OBJECTS_IN_RANGE = "No object found in range."
        NOT_IN_RANGE = "Specified object is not within range."
        NOT_AN_OBJECT = "UseObject action could not be performed, as object doesn't exist."
        RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
        OBJECT_BLOCKED = "Can't use object, another object or agent is blocking the useable object."
        NO_OBJECT_SPECIFIED = "No object_id specified."   
        NO_VALID_USE_TARGET = "No suitable target available for this use action"

        
    def mutate(self, grid_world, agent_id, world_state, **kwargs):
        # fetch options
        #action_range = 1 if 'action_range' not in kwargs else kwargs['action_range']
               
        # object_id is required
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        if object_id == None:
            result = self.Result(self.Result.NO_OBJECT_SPECIFIED, False)
            return result
   
        # get obj
        obj = grid_world.environment_objects[object_id]
        loc_obj_ids = grid_world.grid[obj.location[1], obj.location[0]]
        agent = grid_world.registered_agents[agent_id]
       
        itemstacks = []
        prgs_bar = None
        for obj_id in loc_obj_ids:
            env_obj = grid_world.environment_objects[obj_id]
            if 'stack' in env_obj.custom_properties and env_obj.custom_properties['stack']:
                itemstacks.append(env_obj)
            if 'is_progress' in env_obj.custom_properties and env_obj.custom_properties['is_progress']:
                prgs_bar = env_obj


        if itemstacks != [] and obj.can_use(grid_world=grid_world, itemstacks=itemstacks, use_target=obj, use_agent=agent):
            if prgs_bar:
                prgs_bar.next_stage()
            else:
                prgs_bar = ProgressBar(obj.location, [1, 2, 3, 4])
                grid_world._register_env_object(prgs_bar, ensure_unique_id=True)
        
            result = self.Result(self.Result.RESULT_PROGRESS, True)
            
            if prgs_bar.custom_properties['is_done']:
                obj.use(grid_world=grid_world, itemstacks=itemstacks, use_target=obj, use_agent=agent)
                success = grid_world.remove_from_grid(object_id=prgs_bar.obj_id, remove_from_carrier=False)
                if success:   
                    result = self.Result(self.Result.RESULT_SUCCESS, True)
        
        else:
            result = self.Result(self.Result.NO_VALID_USE_TARGET, True)
            
        return result
    
    def is_possible(self, grid_world, agent_id, world_state, **kwargs):
        # fetch options
        action_range = np.inf if 'action_range' not in kwargs else kwargs['action_range']
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']

        result = _object_interaction_is_possible(grid_world, agent_id, self.Result, object_id, action_range)
        return result
    
class TakeOrPut(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)
        
    def is_possible(self, grid_world, agent_id, world_state, **kwargs):
        assert False, "TakeOrPut action should not be used as proper action!"
        return PrintableActionResult("TakeOrPut action should not be used as proper action!", False)
    
class Take(Action):

    class Result(PrintableActionResult):
        RESULT_SUCCESS = "ItemStack was Taken from object succesfully."
        NO_OBJECTS_IN_RANGE = "No object found in range."
        NOT_IN_RANGE = "Specified object is not within range."
        NOT_AN_OBJECT = "Take action could not be performed, as object doesn't exist."
        RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
        OBJECT_BLOCKED = "Can't Take from object, another object or agent is blocking the useable object."
        NO_OBJECT_SPECIFIED = "No object_id specified."
        EMPTY_ITEMSTACK = "The specified object does not hold an itemStack to Take"  
        FAILED_TO_REMOVE_OBJECT_FROM_WORLD = "Failed to remove the object from the world"
        RESULT_OBJECT_CARRIED = 'Object is already carried'
        RESULT_OBJECT_UNMOVABLE = 'Object is not movable'
            
    def mutate(self, grid_world, agent_id, world_state, **kwargs):
        # fetch options
        #action_range = 1 if 'action_range' not in kwargs else kwargs['action_range']
               
        # object_id is required
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        if object_id == None:
            result = self.Result(self.Result.NO_OBJECT_SPECIFIED, False)
            return result
   
        # get obj and agent
        env_obj = grid_world.environment_objects[object_id]
        agent = grid_world.registered_agents[agent_id]
        
        # take the itemStack from the object
        #stack = obj.take()
        
        if 'is_source' in env_obj.custom_properties and env_obj.custom_properties['is_source']:
            result = _from_source(grid_world, agent, env_obj)
        else:
            result = _take_object(grid_world, agent, env_obj)
        return result
    
    def is_possible(self, grid_world, agent_id, world_state, **kwargs):
        # fetch options
        action_range = np.inf if 'action_range' not in kwargs else kwargs['action_range']
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        max_objects = np.inf if 'max_objects' not in kwargs else kwargs['max_objects']

        # Already carries an object
        if len(grid_world.registered_agents[agent_id].is_carrying) >= max_objects:
            result = self.Result(self.Result.RESULT_CARRIES_OBJECT, False)
            return result

        result = _object_interaction_is_possible(grid_world, agent_id, self.Result, object_id, action_range)

        if result.succeeded and object_id is not None:
            env_obj = grid_world.environment_objects[object_id]  # Environment object

            # Check if the object actually holds a non-empty item stack
            if not env_obj.stack:
                result = self.Result(self.Result.EMPTY_ITEMSTACK, False)
                
            # Check if the object is not carried by another agent
            elif len(env_obj.carried_by) != 0:
                result = self.Result(self.Result.RESULT_OBJECT_CARRIED, False)
            
            elif not (env_obj.properties["is_movable"] or env_obj.custom_properties["is_source"]):
                result = self.Result(self.Result.RESULT_OBJECT_UNMOVABLE, False)
        return result
    
class Put(Action):
    
    class Result(PrintableActionResult):
        RESULT_SUCCESS = 'Put action successfull'
        RESULT_SUCCESS_MERGE = "Put action resulted in succesfull merge"
        RESULT_SUCCESS_TRASH = "Put action resulted in succesfull trash"
        RESULT_SUCCESS_DELIVERY = "Put action resulted in succesfull delivery"
        RESULT_NO_OBJECT = 'The item is not carried'
        RESULT_NONE_GIVEN = "'None' used as input id"
        RESULT_AGENT = 'Cannot drop item on an agent'
        RESULT_UNKNOWN_OBJECT_TYPE = 'Cannot drop item on an unknown object'
        RESULT_NO_OBJECT_CARRIED = 'Cannot drop object when none carried'
        RESULT_ALREADY_OBJECT = "Cannot merge or swap object with already present object"

    def _put_is_possible(self, grid_world, agent_id, obj_id, drop_range):
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    
        # No object given
        if not obj_id:
            return self.Result(self.Result.RESULT_NONE_GIVEN, False)
    
        # No object with that name carried by agent
        if isinstance(obj_id, str) and not any([obj_id == obj.obj_id for obj in reg_ag.is_carrying]):
            return self.Result(self.Result.RESULT_NO_OBJECT, False)
      
        return self.Result(self.Result.RESULT_SUCCESS, True)
 
    def _put_is_valid(self, grid_world, env_obj, drop_location, agent_id):   
        """
        For now, assume it is always okay to put an item somewhere
        """        
        return True
    
    def is_possible(self, grid_world, agent_id, world_state, **kwargs):

        reg_ag = grid_world.registered_agents[agent_id]

        drop_range = 1 if 'drop_range' not in kwargs else kwargs['drop_range']

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
        elif len(reg_ag.is_carrying) > 0:
            obj_id = reg_ag.is_carrying[-1].obj_id
        else:
            return self.Result(self.Result.RESULT_NO_OBJECT_CARRIED, False)

        return self._put_is_possible(grid_world, agent_id=agent_id, obj_id=obj_id, drop_range=drop_range)

    def mutate(self, grid_world, agent_id, world_state, **kwargs):

        reg_ag = grid_world.registered_agents[agent_id]

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
            env_obj = [obj for obj in reg_ag.is_carrying if obj.obj_id == obj_id][0]
        elif len(reg_ag.is_carrying) > 0:
            env_obj = reg_ag.is_carrying[-1]
        else:
            return self.Result(self.Result.RESULT_NO_OBJECT_CARRIED, False)
            
        agent_loc = grid_world.registered_agents[agent_id].location
        agent_dir = grid_world.registered_agents[agent_id].custom_properties['direction']
        dx, dy = Direction.from_name(agent_dir).get_dx_dy()
        target_loc = (agent_loc[0] + dx, agent_loc[1] + dy)

        # check if we can put it at the location we are facing
        curr_loc_put_valid = self._put_is_valid(grid_world, env_obj, target_loc, agent_id)

        # put it in front of the agent if possible
        if curr_loc_put_valid:
            result = _put_object(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=target_loc)

        # if the agent location was the only within range, return a negative action result
        #elif not curr_loc_put_valid and drop_range == 0:
        #    return self.Result(self.Result.RESULT_OBJECT, False)

        # Try finding other drop locations from close to further away around the agent
        #drop_loc = _find_drop_loc(grid_world, reg_ag, env_obj, drop_range, reg_ag.location)

        # If we didn't find a valid drop location within range, return a negative action result
        #if not drop_loc:
        return result

        #return _put_object(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=drop_loc)
    
    
def _object_interaction_is_possible(grid_world, agent_id, action_result, object_id=None, action_range=np.inf):
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location  # Agent location

    # check if there is an object in the scenario
    objects_in_range = grid_world.get_objects_in_range(loc_agent, object_type=None, sense_range=action_range)

    # There is no object in range
    if len(objects_in_range) == 0:
        return action_result(action_result.NO_OBJECTS_IN_RANGE, False)

    # if we did not get a specific object to target, we simply return success
    if object_id is None:
       return action_result(action_result.RESULT_SUCCESS, True)

    # check if the given object_id even exists
    if object_id not in grid_world.environment_objects.keys():
        return action_result(action_result.NOT_AN_OBJECT, False)

    # check if the given object_id is in range
    if object_id not in objects_in_range.keys():
        return action_result(action_result.NOT_IN_RANGE, False)

    return action_result(action_result.RESULT_SUCCESS, True)

def _from_source(grid_world, agent, src_obj):
    new_itemstack = src_obj.new_stack(src_obj.location, agent)
    #grid_world._register_env_object(new_itemstack, ensure_unique_id=True)
    _take_object(grid_world, agent, new_itemstack, remove_from_grid=False)    

    return Take.Result(Take.Result.RESULT_SUCCESS, True)

def _take_object(grid_world, agent, env_obj, remove_from_grid=True):  
    # Updating properties
    env_obj.carried_by.append(agent.obj_id)
    agent.is_carrying.append(env_obj)  # we add the entire object!
    
    if remove_from_grid:
        success = grid_world.remove_from_grid(object_id=env_obj.obj_id, remove_from_carrier=False)
        if not success:
            return Take.Result(Take.Result.FAILED_TO_REMOVE_OBJECT_FROM_WORLD, False)
    
    # If this item was being processed, its progress is reset
    _remove_progress_objects(grid_world, env_obj.location)
    
    # Updating Location
    env_obj.location = agent.location
    
    # Save the avatar's base image if that wasn't already done
    if not 'base_img' in agent.custom_properties:
        agent.custom_properties['base_img']=agent.custom_properties['img_name']
    
    # Update the avatar img to signal they are holding the itemStack
    if agent.custom_properties['direction'] == Direction.South().name:
        new_path = overlay_image(overlay=env_obj.custom_properties['img_name'], base=agent.custom_properties['base_img'], box=(0.3, 0.6, 0.7, 1.0))  
        agent.custom_properties['img_name']=new_path

    return Take.Result(Take.Result.RESULT_SUCCESS, True)

def _put_object(grid_world, agent, env_obj, drop_loc):
    # Updating properties
    agent.is_carrying.remove(env_obj)
    env_obj.carried_by.remove(agent.obj_id)
    
    # Reset the image of the avatar
    agent.custom_properties['img_name'] = agent.custom_properties['base_img']
    
    # See if we can merge with an existing itemstack
    loc_obj_ids = grid_world.grid[drop_loc[1], drop_loc[0]]
    
    
    for obj_id in loc_obj_ids:

        if obj_id is not env_obj.obj_id and obj_id not in grid_world.registered_agents:
            stack_obj = grid_world.environment_objects[obj_id]
            if 'is_delivery' in stack_obj.custom_properties and stack_obj.custom_properties['is_delivery']:
                if stack_obj.deliver_stack(env_obj, grid_world.current_nr_ticks):
                    return Put.Result(Put.Result.RESULT_SUCCESS_DELIVERY, True)
            elif 'is_trash' in stack_obj.custom_properties and stack_obj.custom_properties['is_trash']:
                return Put.Result(Put.Result.RESULT_SUCCESS_TRASH, True)
            elif 'is_source' in stack_obj.custom_properties and stack_obj.custom_properties['is_source']:
                continue
            elif 'stack' in stack_obj.custom_properties and stack_obj.custom_properties['stack']:
                if stack_obj.merge_stack(env_obj, agent):
                    # If this item was being processed, its progress is reset
                    _remove_progress_objects(grid_world, stack_obj.location)
                    
                    # if we successfully merged, we are done here
                    return Put.Result(Put.Result.RESULT_SUCCESS_MERGE, True)
                else:
                    # if we cannot merge, we try to swap
                    success = _take_object(grid_world, agent, stack_obj)
                    if not success.succeeded:
                        return Put.Result(Put.Result.RESULT_ALREADY_OBJECT, False)

    # If we did not succesfully merge, return the object to the grid
    env_obj.location = drop_loc
    grid_world._register_env_object(env_obj, ensure_unique_id=True)

    return Put.Result(Put.Result.RESULT_SUCCESS, True)

def _remove_progress_objects(grid_world, location):
    loc_obj_ids = grid_world.grid[location[1], location[0]]
    
    for obj_id in loc_obj_ids:
        env_obj = grid_world.environment_objects[obj_id]
        if 'is_progress' in env_obj.custom_properties and env_obj.custom_properties['is_progress']:
            grid_world.remove_from_grid(object_id=env_obj.obj_id, remove_from_carrier=False)

class TurnAndMove(Move):
    
    class _DirectionalMove(Move):
        def __init__(self, direction=None):
            super().__init__()
            self.direction = direction
            self.dx, self.dy = self.direction.get_dx_dy()

        def is_possible(self, grid_world, agent_id, world_state, **kwargs):
            result = super().is_possible(grid_world, agent_id, world_state)
            
            #turning is always possible, hence we always do a turn before returning the result
            agent = grid_world.registered_agents[agent_id]
            if agent.custom_properties['direction'] != self.direction.name:
                # turn the agent internally
                agent.custom_properties['direction'] = self.direction.name
                
                # Save the avatar's base image if that wasn't already done
                if not 'base_img' in agent.custom_properties:
                    agent.custom_properties['base_img']=agent.custom_properties['img_name']
                
                # Update the base img to reflect the new direction
                new_path = self.direction.directional_img(agent.custom_properties['base_img'])
                agent.custom_properties['base_img']=new_path
                
                # If the agent is looking south, update with the item it is carrying (if any)
                if agent.is_carrying and self.direction.name == Direction.South().name:
                    obj = agent.is_carrying[-1]
                    new_path = overlay_image(overlay=obj.custom_properties['img_name'], base=agent.custom_properties['base_img'], box=(0.3, 0.6, 0.7, 1.0))  
                
                agent.custom_properties['img_name']=new_path
                return PrintableActionResult("Agent was not facing the right direction, turned instead", False)
            
            return result
    
    class North(_DirectionalMove):
        def __init__(self):
            super().__init__(direction=Direction.North())

    class East(_DirectionalMove):
        def __init__(self):
            super().__init__(direction=Direction.East())
            
    class South(_DirectionalMove):
        def __init__(self):
            super().__init__(direction=Direction.South())
            
    class West(_DirectionalMove):
        def __init__(self):
            super().__init__(direction=Direction.West())
            
    def from_move_action(move_action): 
        if move_action == MoveNorth.__name__:
            return TurnAndMove.North.__name__
        if move_action == MoveSouth.__name__:
            return TurnAndMove.South.__name__
        if move_action == MoveWest.__name__:
            return TurnAndMove.West.__name__
        if move_action == MoveEast.__name__:
            return TurnAndMove.East.__name__
        return move_action
    
    def from_direction(direction):
        if direction.img_append == Direction.direction_paths[0]:
            return TurnAndMove.North.__name__
        if direction.img_append == Direction.direction_paths[1]:
            return TurnAndMove.East.__name__
        if direction.img_append == Direction.direction_paths[2]:
            return TurnAndMove.South.__name__
        if direction.img_append == Direction.direction_paths[3]:
            return TurnAndMove.West.__name__
