# -*- coding: utf-8 -*-
"""
Created on Tue May 30 13:09:14 2023

@author: cornelissennaj
"""

from matrx.agents import HumanAgentBrain, AgentBrain
from matrx.agents.agent_utils.navigator import Navigator
from matrx.agents.agent_utils.state_tracker import StateTracker
from matrx.actions.move_actions import MoveNorthEast, MoveNorthWest, MoveSouthEast, MoveSouthWest

from .actions import Use, Take, Put, TakeOrPut, TurnAndMove
from .util import Direction
from .recipes import Recipe
from .predicates import Chopped
from .tasks import Task, TaskType, TaskId
from enum import Enum

"""
Simple Enum to keep track of agent types
"""
class AgentType(str, Enum):
    HUMAN = "human"
    TASK_BASED ="task_based"
    PLAY_BASED = "play_based"
    GOAL_BASED = "goal_based"
    NO_AGENT = None

class HumanCookBrain(HumanAgentBrain):
    
    def __init__(self, memorize_for_ticks=None, use_range=1, direction=Direction.North):
        self.use_range = use_range
        self.max_carry_objects = 1
        self.grab_range = 1
        self.drop_range = 1
        self.direction = direction
        
        self.move_speed = 2
        self.use_speed = 2
        self.take_speed = 1
        self.put_speed = 1
        
        super().__init__(memorize_for_ticks, fov_occlusion=False, max_carry_objects=self.max_carry_objects,
                 grab_range=self.grab_range, drop_range=self.drop_range, door_range=1, remove_range=1)
    
    def initialize(self):
        super().initialize()
        
    def filter_observations(self, state):
        return super().filter_observations(state)
    
    def decide_on_action(self, state, user_input):
        action_kwargs = {}
        action = None
        
        # if no keys were pressed, do nothing
        if user_input is None or user_input == []:
            return action, action_kwargs

        # take the latest pressed key (for now), and fetch the action
        # associated with that key
        pressed_keys = user_input[-1]
        action = self.key_action_map[pressed_keys]

        if action == Use.__name__:
            return _use_action(self, state, (action, action_kwargs))

        elif action == TakeOrPut.__name__:
            return _take_or_put_action(self, state, (action, action_kwargs))
        
        return action, action_kwargs
    
    def create_context_menu_for_self(self, clicked_object_id, click_location,
                                     self_selected):
        return []

    def create_context_menu_for_other(self, agent_id_who_clicked,
                                     clicked_object_id, click_location):
        return []


class ArtificialCookBrain(AgentBrain):
    
    def __init__(self, recipeBook, memorize_for_ticks=None, move_speed=15, use_range=1, direction=Direction.North):
        super().__init__(memorize_for_ticks)
        self.recipeBook = recipeBook
        
        self.use_range = use_range
        self.max_carry_objects = 1 #multiple carried objects currently not supported in agent behaviour
        self.grab_range = 1
        self.drop_range = 1
        self.direction = direction
        self.state_tracker = None
        self.navigator = None
        self.waypoints = []
        self.task_mark = 0
        
        """
        Tune-able parameters (e.g. using priorities or plays)
        """
        self.move_speed = 3
        self.use_speed = 4
        self.take_speed = 4
        self.put_speed = 4
        
    def initialize(self):
        super().initialize()

        # Initialize this agent's state tracker
        self.state_tracker = StateTracker(agent_id=self.agent_id)

        # Remove diagonal movements
        self.action_set.remove(MoveNorthEast.__name__)
        self.action_set.remove(MoveNorthWest.__name__)
        self.action_set.remove(MoveSouthEast.__name__)
        self.action_set.remove(MoveSouthWest.__name__)

        # Initialize this agent's navigator
        self.navigator = Navigator(agent_id=self.agent_id, action_set=self.action_set)
        self.navigator.add_waypoints(self.waypoints, is_circular=False)
        
        
    def filter_observations(self, state):
        self.state_tracker.update(state)
        return state    
    
    def decide_on_action(self, state):
        assert False, "ArtificalCookBrain is a template, not ready for use, must implement decide_on_action(self, state)"
        return None, {}
    
class TaskBasedCookBrain(ArtificialCookBrain):   
    def decide_on_action(self, state):
        action, action_kwargs = None, {}
        self.decode_task_messages(state)
        
        return _do_next_task(self, state, args=(action, action_kwargs))
    
    """
    Decode any new messages and add them to task list if necessary
    """
    def decode_task_messages(self, state, seen='(seen)'):
        body = state[self.agent_id]
        
        for i in range(len(self.received_messages)):
    
            if not self.received_messages[i].endswith(seen):   
                _, _, msg = self.received_messages[i].partition('Please ')
                task_type, _, msg = msg.partition(' ')
                _, _, target = msg.rpartition(' ')
                target, _, _ = target.rpartition('.')
                self.received_messages[i] += seen
                            
                if task_type == TaskType.MAKE_AND_SERVE or task_type == TaskType.SERVE or task_type == TaskType.PREPARE or task_type == TaskType.GET:
                    recipe = self.recipeBook.get_recipe(target)
                    if recipe is not None:
                        task = Task(task_type=task_type, unique_name=recipe.get_unique_name(),
                                             display_name=recipe.get_display_name(),
                                             resource_name=recipe.get_img(),
                                             mark=self.agent_id+str(self.task_mark)  )
                        self.task_mark += 1
                        body['queued_tasks'].append( task )

                elif task_type == TaskType.MOVE:
                    obj_id = _find_reachable_property_in_state(state, self, 'search_name', target)
                    if obj_id is not None:
                        obj = state[obj_id]
                        task = Task(task_type=task_type, unique_name=target,
                                             display_name=obj['display_name'],
                                             resource_name=obj['img_name'],
                                             mark=self.agent_id+str(self.task_mark) )
                        
                        self.task_mark += 1
                        body['queued_tasks'].append( task )
                        
                elif task_type == TaskType.USE:
                    use_task = None
                    for u_t in body['use_tasks']:
                        if u_t['unique_name']:
                            use_task = u_t
                        
                    if use_task is not None:
                        task = Task(task_type=task_type, unique_name=target,
                                            display_name=use_task['display_name'],
                                            resource_name=use_task['resource_name'],
                                            mark=self.agent_id+str(self.task_mark) )
                        self.task_mark += 1
                        body['queued_tasks'].append( task )
                    
                elif task_type == TaskType.CANCEL:
                    for i in reversed(range(len(body['queued_tasks']))):
                        if body['queued_tasks'][i].mark == target:
                            body['queued_tasks'].pop(i)

class GoalBasedCookBrain(ArtificialCookBrain):
    INIT_LIABILITIES = []
    
    def decide_on_action(self, state):
        action, action_kwargs = None, {}        
        self.decode_task_messages(state)
        body = state[self.agent_id]
        
        if TaskId.NONE in body['active_priorities']:
            return action, action_kwargs
        
        del_id = _find_property_in_state(state, 'is_delivery', True)
        if del_id is None:
            return action, action_kwargs
    
        goals = state[del_id]['goals']
        if not goals:
            return action, action_kwargs
        
        self.update_tasks_using_goals(body, goals, state['nr_ticks']['nr_ticks'])
                                    
        action, action_kwargs = _do_next_task(self, state, args=(action, action_kwargs))
        #if action is None:
        #    new_loc = _find_item_drop_loc_near_loc(self, body['location'], state, max_radius=3, require_counter=True)
        #    action, action_kwargs = _move_adj_to_loc(new_loc, state, self)
        return action, action_kwargs

    """
    Decode any new messages and add them to task list if necessary
    """
    def decode_task_messages(self, state, seen='(seen)'):
        body = state[self.agent_id]

        for i in range(len(self.received_messages)):
    
            if not self.received_messages[i].endswith(seen):
                """
                We expect messages of the format "{word} {task_type} {word} {target}."
                """
                _, _, msg = self.received_messages[i].partition(' ')
                task_type, _, msg = msg.partition(' ')
                _, _, target = msg.rpartition(' ')
                target, _, _ = target.rpartition('.')
                self.received_messages[i] += seen
                                
                if task_type == TaskType.PRIORITY:
                    self.switch_priority(target, state)
                
                elif task_type == TaskType.CANCEL:
                    for i in reversed(range(len(body['queued_tasks']))):
                        if body['queued_tasks'][i].mark == target:
                            body['queued_tasks'].pop(i)

    def update_tasks_using_goals(self, agent_body, goals, currentTick):
        task_marks = [t['mark'].split(self.agent_id)[0] for t in agent_body['queued_tasks']] 
        goal_marks = [g['target']['mark'] for g in goals] 
    
        # First we clear any queued task that is not a goal
        for i in reversed(range(len(task_marks))):
            if task_marks[i] not in goal_marks:
                agent_body['queued_tasks'].pop(i)
        
        # Then we add any new goals to the task queue                
        for g in goals:
            if g['appears_at']+5 <= currentTick and g['max_nr_ticks'] > currentTick:
                goal, reward = g['target'], g['max_reward']
                if not goal['mark'] in task_marks:
                    task = Task(task_type=TaskType.MAKE_AND_SERVE, unique_name=goal['unique_name'],
                        display_name=goal['display_name'],
                        resource_name=goal['resource_name'],
                        mark=goal['mark'] + self.agent_id+str(self.task_mark)  )
                    self.task_mark += 1
                    agent_body['queued_tasks'].append( task ) 
                    
    def switch_priority(self, priority, state):
        body = state[self.agent_id]
        
        # If we did not already save our liabilities, do so now
        if not self.INIT_LIABILITIES:
            self.INIT_LIABILITIES = body['reliability']['liabilities']
        
        # make sure we reference the original list because apparently matrx keeps a hard copy
        body['active_priorities'].clear()
        body['active_priorities'].append(priority)
        
        if priority == TaskId.NONE:
            body['queued_tasks'].clear()
        
        if priority == TaskId.PRIO_SPEED:
            """
            Tune-able parameters (e.g. using priorities or plays)
            """
            self.move_speed = 2
            self.use_speed = 2
            self.take_speed = 2
            self.put_speed = 2
            body['reliability']['liabilities'] = self.INIT_LIABILITIES

        if priority == TaskId.PRIO_SAFETY:
            """
            Tune-able parameters (e.g. using priorities or plays)
            """
            self.move_speed = 6
            self.use_speed = 4
            self.take_speed = 4
            self.put_speed = 4
            body['reliability']['liabilities'] = self.INIT_LIABILITIES
            
        if priority == TaskId.PRIO_QUALITY:
            """
            Tune-able parameters (e.g. using priorities or plays)
            """
            self.move_speed = 3
            self.use_speed = 8
            self.take_speed = 4
            self.put_speed = 4
            body['reliability']['liabilities'] = []
            
        
class PlayBasedCookBrain(ArtificialCookBrain):
    def decide_on_action(self, state):
        action, action_kwargs = None, {}
        self.decode_task_messages(state)
        body = state[self.agent_id]
        
        if TaskId.NONE in body['active_plays']:
            return action, action_kwargs
        
        del_id = _find_property_in_state(state, 'is_delivery', True)
        if del_id is None:
            return action, action_kwargs
    
        goals = state[del_id]['goals']
        if not goals:
            return action, action_kwargs
                
        self.divide_tasks_using_goals(body, goals, state['nr_ticks']['nr_ticks'], body['action_whitelist'])
        
        action, action_kwargs = _do_next_task(self, state, args=(action, action_kwargs))
        #if action is None:
        #    new_loc = _find_item_drop_loc_near_loc(self, body['location'], state, max_radius=3, require_counter=True)
        #    action, action_kwargs = _move_adj_to_loc(new_loc, state, self)
        return action, action_kwargs


    """
    Decode any new messages and add them to task list if necessary
    """
    def decode_task_messages(self, state, seen='(seen)'):
        body = state[self.agent_id]

        for i in range(len(self.received_messages)):
    
            if not self.received_messages[i].endswith(seen):
                """
                We expect messages of the format "{word} {task_type} {word} {target}."
                """
                _, _, msg = self.received_messages[i].partition(' ')
                task_type, _, msg = msg.partition(' ')
                _, _, target = msg.rpartition(' ')
                target, _, _ = target.rpartition('.')
                self.received_messages[i] += seen
            
                if task_type == TaskType.PLAY:
                    self.switch_play(target, state)
                
                elif task_type == TaskType.CANCEL:
                    for i in reversed(range(len(body['queued_tasks']))):
                        if body['queued_tasks'][i].mark == target:
                            body['queued_tasks'].pop(i)


    def divide_tasks_using_goals(self, agent_body, goals, currentTick, whitelist, delimiter='_sub_'):
        task_marks = [t['mark'].split(self.agent_id)[0] for t in agent_body['queued_tasks']] 
        goal_marks = [g['target']['mark'] for g in goals] 
        completed_marks = [t.split(self.agent_id)[0] for t in agent_body['completed_tasks']] 
    
        # First we clear any queued task that is not part of a current goal
        for i in reversed(range(len(task_marks))):
            if task_marks[i].split(delimiter)[0] not in goal_marks:
                agent_body['queued_tasks'].pop(i)
    
        # Then we add any new goals to the task queue                
        for g in goals:
            # we add 50 ticks to make the agent a bit 'slower' at interpreting incoming goals
            if g['appears_at']+5 <= currentTick and g['max_nr_ticks'] > currentTick:
                goal, reward = g['target'], g['max_reward']
                goal = Recipe.from_json_gen(goal)
                
                new_tasks = []
                                
                if TaskId.PLAY_SERVE in agent_body['active_plays']:
                    mark = goal.mark+delimiter + "SERVE"
                    if (goal in whitelist) and (mark not in task_marks) and (mark not in completed_marks):
                        task = Task(task_type=TaskType.SERVE, unique_name=goal.get_unique_name(),
                                    display_name=goal.get_display_name(),
                                    resource_name=goal.get_img(),
                                    mark=mark + self.agent_id+str(self.task_mark)  )
                        self.task_mark += 1
                        new_tasks.append( task )
                
                if TaskId.PLAY_ASSEMBLE in agent_body['active_plays']:
                    mark = goal.mark+delimiter + "PREPARE"
                    if (goal in whitelist) and (mark not in task_marks) and (mark not in completed_marks):
                        task = Task(task_type=TaskType.PREPARE, unique_name=goal.get_unique_name(),
                                    display_name=goal.get_display_name(),
                                    resource_name=goal.get_img(),
                                    mark=mark + self.agent_id+str(self.task_mark)  )
                        self.task_mark += 1
                        new_tasks.append( task )
                
                if TaskId.PLAY_VEG in agent_body['active_plays']:
                    subs = goal.get_subtasks()
                    while subs:
                        subt_a, subt_b = subs[0]
                        subs = []
        
                        mark = goal.mark+delimiter+subt_a.get_unique_name()
                        if (subt_a in whitelist) and (mark not in task_marks) and (mark not in completed_marks):
                            task = Task(task_type=TaskType.PREPARE, unique_name=subt_a.get_unique_name(),
                                        display_name=subt_a.get_display_name(),
                                        resource_name=subt_a.get_img(),
                                        mark=mark + self.agent_id+str(self.task_mark)  )
                            self.task_mark += 1
                            new_tasks.append( task )
        
                        if isinstance(subt_b, Recipe):
                            mark = goal.mark+delimiter+subt_b.get_unique_name()
                            if not subt_b in whitelist:
                                subs = subt_b.get_subtasks()
                            elif (mark not in task_marks) and (mark not in completed_marks):
                                task = Task(task_type=TaskType.PREPARE, unique_name=subt_b.get_unique_name(),
                                            display_name=subt_b.get_display_name(),
                                            resource_name=subt_b.get_img(),
                                            mark=mark + self.agent_id+str(self.task_mark)  )
                                self.task_mark += 1
                                new_tasks.append( task )
                            
                if new_tasks: agent_body['queued_tasks'].extend(new_tasks)
                            
    def switch_play(self, play, state):
        body = state[self.agent_id]
        
        # make sure we reference the original list because apparently matrx keeps a hard copy
        body['active_plays'].clear()
        body['active_plays'].append(play)
        
        # make sure we reference the original list because apparently matrx keeps a hard copy
        body['action_whitelist'].clear()
        body['queued_tasks'].clear()
        body['completed_tasks'].clear()

        
        if play == TaskId.PLAY_ASSEMBLE:
            body['action_whitelist'].extend( list(set(body['recipeBook']['merge_recipes']))  )
        if play == TaskId.PLAY_SERVE:
            body['action_whitelist'].extend( list(body['recipeBook']['deliverables'])  )
        if play == TaskId.PLAY_VEG:
            body['action_whitelist'].extend( list(body['recipeBook']['tool_recipes'][Chopped.name].values())  )

"""
Do the next task in queue
"""
def _do_next_task(agent, state, args=(None, {})):
    action, action_kwargs = args
    body = state[agent.agent_id]
    if not body['queued_tasks']:
        return None, {}
    
    first_task = body['queued_tasks'][0]
    task_type = first_task.task_type
    
    if task_type == TaskType.MAKE_AND_SERVE or task_type == TaskType.SERVE or task_type == TaskType.PREPARE or task_type == TaskType.GET:
        action, action_kwargs = _decide_on_recipe_action(first_task, agent, state, args=(action, action_kwargs))
    elif task_type == TaskType.MOVE:
        action, action_kwargs = _decide_on_move_action(first_task, agent, state, args=(action, action_kwargs))
    elif task_type == TaskType.USE:
        action, action_kwargs = _decide_on_use_action(first_task, agent, state, args=(action, action_kwargs))
            
    if 'success' in action_kwargs:
        body['completed_tasks'].append(body['queued_tasks'].pop(0)['mark'])
        
    return action, action_kwargs


"""
Determine the behaviour for the 'serve', 'prepare' and 'get' actions
"""
def _decide_on_recipe_action(task, agent, state, args=(None, {})):
    action, action_kwargs = args
    body = state[agent.agent_id]
    task_type = task.task_type
    task_recipe = agent.recipeBook.get_recipe(task.unique_name)
    task_recipe.set_mark(task.mark)
    
    should_serve = (task_type == TaskType.MAKE_AND_SERVE or task_type == TaskType.SERVE)
    
    if _is_holding_itemstack(agent, task_recipe, state, ignore_mark=True):
        if body['is_carrying'][0]['stack']['mark'] is None:
            body['is_carrying'][0]['stack']['mark'] = task.mark
    
        if should_serve and _is_holding_itemstack(agent, task_recipe, state, ignore_mark=True):
            action, action_kwargs = _deliver_itemstack(agent, state, (action, action_kwargs))
        
        elif task_type == TaskType.PREPARE and _is_holding_itemstack(agent, task_recipe, state, ignore_mark=False):
            loc = _find_item_drop_loc_near_agent(agent, state, max_radius=5, require_counter=True)
            action, action_kwargs = _put_itemstack(agent, loc, state, (action, action_kwargs))
   
        elif task_type == TaskType.GET and _is_holding_itemstack(agent, task_recipe, state, ignore_mark=False):
            action, action_kwargs = TurnAndMove.South.__name__, {'success': True}
    
    else:
        obj_id = _find_itemstack_in_state(task_recipe, state, ignore_mark=should_serve)
        action, action_kwargs = _fetch_itemstack_in_state(agent, obj_id, state, (action, action_kwargs))
        if 'success' in action_kwargs:
            action_kwargs.pop('success') # even if this action is complete, our task is not finished

    if action is None:
        whitelist = []
        if 'action_whitelist' in body:
            whitelist = body['action_whitelist']
        
        max_depth = 0 if task_type == TaskType.SERVE else float('inf')
        action, action_kwargs = _perform_subtasks([(task_recipe, None)], state, agent, args=(action, action_kwargs), ignore_mark=should_serve, whitelist=whitelist, max_depth=max_depth)
        if 'success' in action_kwargs:
            action_kwargs.pop('success') # even if this action is complete, our task is not finished
        
    return action, action_kwargs

"""
Determine the behaviour for the 'use' action
"""
def _decide_on_use_action(task, agent, state, args=(None, {})):
    action, action_kwargs = args

    obj_id = _select_facing_object(agent, state,
                                          property_to_check="is_usable")
    if obj_id is None:
        return None, {'success' : False}
    
    item_id = _select_facing_object(agent, state,
                                          property_to_check="stack")
    
    if item_id is None and state[agent.agent_id]['is_carrying']:
        return _put_action(agent, state, (action, action_kwargs))
    
    prgs_id = _select_facing_object(agent, state,
                                          property_to_check="almost_done")
    if prgs_id:
        action_kwargs['success'] = True
        
    return _use_action(agent, state, (action, action_kwargs))

"""
Determine the behaviour for the 'move' action
"""
def _decide_on_move_action(task, agent, state, args=(None, {})):
    action, action_kwargs = args
    
    if not state[agent.agent_id]['is_carrying']:
        obj_id = _select_facing_object(agent, state,
                                          property_to_check="stack")  
        if obj_id is not None:
            return _take_action(agent, state, (action, action_kwargs))
    
    obj_id = _find_reachable_property_in_state(state, agent, 'search_name', task['unique_name'])
    if obj_id is not None:
        obj = state[obj_id]
        if 'isAgent' in obj and obj['isAgent']: #quick and dirty way to check if this is an agent
            loc = _find_item_drop_loc_near_loc(agent, obj['location'], state, max_radius=4, require_counter=True)
            action, action_kwargs = _put_itemstack(agent, loc, state, (action, action_kwargs))
        else:    
            action, action_kwargs = _put_itemstack(agent, obj['location'], state, (action, action_kwargs))
    
    return action, action_kwargs

def _use_action(cook, state, args=(None, {})):
    action, action_kwargs = args
    action_kwargs['action_range'] = cook.use_range

    obj_id = _select_facing_object(cook, state,
                                          property_to_check="is_usable")   
    
    action_kwargs['object_id'] = obj_id
    action_kwargs["action_duration"] = cook.use_speed

    return Use.__name__, action_kwargs

def _take_action(cook, state, args=(None, {})):
    action, action_kwargs = args
    action_kwargs['action_range'] = cook.grab_range

    # First check if the agent is facing any movable object
    obj_id = None
    obj_id = _select_facing_object(cook, state,
                                      property_to_check="is_movable")
    
    # Then check if the agent is facing a source block
    if obj_id is None:
        obj_id = _select_facing_object(cook, state,
                                       property_to_check="is_source")
    
    action_kwargs['object_id'] = obj_id
    action_kwargs["action_duration"] = cook.take_speed

    return Take.__name__, action_kwargs

def _take_or_put_action(cook, state, args=(None, {})):
    if len(state[cook.agent_id]['is_carrying']) < cook.max_carry_objects:
        return _take_action(cook, state, args)
    else:
        return _put_action(cook, state, args)

def _put_action(cook, state, args=(None, {})):
    action, action_kwargs = args
    action_kwargs['drop_range'] = cook.drop_range
    action_kwargs["action_duration"] = cook.put_speed
    return Put.__name__, action_kwargs

def _move_action(cook, state, args=(None, {})):
    action, action_kwargs = args
    action_kwargs["action_duration"] = cook.move_speed
    
    return action, action_kwargs

def _select_facing_object(cook, state, property_to_check=None):
     # Get all perceived objects
    object_ids = list(state.keys())

    agent_loc = state[cook.agent_id]['location']
    agent_dir = state[cook.agent_id]['direction']
    dx, dy = Direction.from_name(agent_dir).get_dx_dy()
    target_loc = (agent_loc[0] + dx, agent_loc[1] + dy)
    
    for object_id in object_ids:
        if 'location' in state[object_id]:
            loc = state[object_id]['location']
            if loc[0] is target_loc[0] and loc[1] is target_loc[1]:
                if property_to_check is None:
                    return object_id
                elif property_to_check in state[object_id] and state[object_id][property_to_check]:
                    return object_id
    return None

def _is_holding_itemstack(agent, recipe, state, ignore_mark=True):
    if state[agent.agent_id]['is_carrying']:
        for item in state[agent.agent_id]['is_carrying']:
            if 'stack' in item and item['stack'] == recipe:
                if ignore_mark or item['stack']['mark'] == recipe.mark: 
                    return True
    return False
    
def _deliver_itemstack(ai_cook, state, args=(None, {})):
    obj_id = _find_property_in_state(state, 'is_delivery', True)
    if obj_id is None:
        return args
    
    obj_loc = state[obj_id]['location']
    return _put_itemstack_in_state(ai_cook, obj_loc, state, args=args)


def _put_itemstack(ai_cook, location, state, args=(None, {})):
    action, action_kwargs = _move_adj_to_loc(location, state, ai_cook, args)
    
    if 'success' in action_kwargs:
        if action_kwargs['success']:
            return _put_action(ai_cook, state, (action, action_kwargs))
        else:
            print("Agent was not able to move in to location")
    return action, action_kwargs

def _find_itemstack_at(target_loc, state):
    object_ids = list(state.keys())
    
    for object_id in object_ids:
        if 'location' in state[object_id]:
            loc = state[object_id]['location']
            if loc[0] is target_loc[0] and loc[1] is target_loc[1]:
                if 'stack' in state[object_id] and state[object_id]['stack']:
                    return object_id
    return None

def _find_usable_in_state(state, use_type):
    object_ids = list(state.keys())
    
    for object_id in object_ids: 
        if 'is_usable' in state[object_id] and state[object_id]['is_usable']:
            if 'use_type' in state[object_id] and state[object_id]['use_type'] == use_type:
               return object_id
    return None

def _find_property_in_state(state, property_, value_):
    object_ids = list(state.keys())
        
    for object_id in object_ids:      
        obj = state[object_id]
        if property_ in obj and obj[property_] == value_:
            return object_id
    return None

def _find_reachable_property_in_state(state, agent, property_, value_):
    object_ids = list(state.keys())
        
    for object_id in object_ids:      
        obj = state[object_id]
        if property_ in obj and obj[property_] == value_:
            action, action_kwargs = _move_adj_to_loc(obj['location'], state, agent)
            if not 'success' in action_kwargs or action_kwargs['success'] == True:
                return object_id
    return None

    
def _find_itemstack_in_state(recipe, state, ignore_source=False, ignore_mark=True):
    object_ids = list(state.keys())
        
    # We loop over the reversed id's to give newer items priority (LIFO)
    for object_id in reversed(object_ids):      
        item = state[object_id]
        if 'stack' in item and item['stack']:
            if item['stack'] == recipe:
                # if we ignore sources then sources should not return obj_id
                should_ignore = ignore_source and 'is_source' in item and item['is_source']
                if not should_ignore and (ignore_mark or item['stack']['mark'] == recipe.mark or item['stack']['mark'] is None):
                    return object_id
    return None

def _is_itemstack_at_location(recipe, location, state):
    object_ids = list(state.keys())
        
    for object_id in object_ids: 
        if 'location' in state[object_id]:
            obj_loc = state[object_id]['location']
            if obj_loc[0] == location[0] and obj_loc[1] == location[1]:    
                if 'stack' in state[object_id] and state[object_id]['stack']:
                    if state[object_id]['stack'] == recipe:
                        #if not 'carried_by' in state[object_id] or not state[object_id]['carried_by']:
                        return True
    return False

def _fetch_itemstack_in_state(ai_cook, obj_id, state, args=(None, {})):
    if not obj_id is None:
        obj_loc = state[obj_id]['location']
        action, action_kwargs = _move_adj_to_loc(obj_loc, state, ai_cook, args)
        if 'success' in action_kwargs:
            if action_kwargs['success']:
                action_kwargs.pop('success')
                return _take_or_put_action(ai_cook, state, (action, action_kwargs))
            else:
                print("Agent was not able to move in to itemstack loc, attempting to move near")
                new_loc = _find_traversable_loc_near_loc(ai_cook, obj_loc, state, max_radius=3)
                return _move_adj_to_loc(new_loc, state, ai_cook, args)
        return action, action_kwargs
    return args

def _put_itemstack_in_state(ai_cook, put_loc, state, args=(None, {})):
    if not put_loc is None:
        action, action_kwargs = _move_adj_to_loc(put_loc, state, ai_cook, args)
        if 'success' in action_kwargs:
            if action_kwargs['success']:
                action_kwargs.pop('success')
                return _put_action(ai_cook, state, (action, action_kwargs))
            else:
                print("Agent was not able to move in to drop loc, attempting to move near")
                new_loc = _find_traversable_loc_near_loc(ai_cook, put_loc, state, max_radius=3)
                return _move_adj_to_loc(new_loc, state, ai_cook, args)
        return action, action_kwargs
    return args

def _move_adj_to_loc(location, state, ai_cook, args=(None, {})):
    agent_loc = state[ai_cook.agent_id]['location']
    agent_dir = state[ai_cook.agent_id]['direction']
    
    target_loc, target_dir = _find_unoccupied_adj_loc(location, state, agent_loc)
    if target_loc is None:
        return (args[0], {'success' : False})
    
    if agent_loc == target_loc:
        if agent_dir == target_dir.img_append:
            return (args[0], {'success' : True})
        else:
            return _move_action(ai_cook, state, (TurnAndMove.from_direction(target_dir), args[1]))
            
    # If the agent does not have a waypoint, or the waypoint does not match the current waypoint, add a waypoint
    #if (not ai_cook.navigator.get_all_waypoints()) or ai_cook.navigator or (not ai_cook.navigator.get_current_waypoint() == target_loc):
    ai_cook.navigator.reset_full()
    ai_cook.navigator.add_waypoint(target_loc)
    move_action = ai_cook.navigator.get_move_action(ai_cook.state_tracker)
    return _move_action(ai_cook, state, (TurnAndMove.from_move_action(move_action), args[1]))
    

def _find_item_drop_loc_near_agent(agent, state, max_radius=3, require_counter=False):
    
    # first check if the area the agent is facing is not already unnoccupied
    ag = state[agent.agent_id]
    agent_loc = ag['location']
    agent_dir = Direction.from_name(ag['direction'])
    dx, dy = agent_dir.get_dx_dy()
    adj_loc = (agent_loc[0] + dx, agent_loc[1] + dy)
    if _is_suitable_drop_loc(adj_loc, state, require_counter):
        return adj_loc
        
    return _find_item_drop_loc_near_loc(agent, agent_loc, state, max_radius=max_radius, require_counter=require_counter)

def _find_traversable_loc_near_loc(agent, start_loc, state, max_radius=3):
    
    ag = state[agent.agent_id]
    agent_loc = ag['location']

    # Spiral outwards towards a drop loation
    spiral_dir = Direction.East()
    adj_loc = start_loc
    max_segment_len = 1
    cur_segment_len = 0
    while abs(adj_loc[0] - start_loc[0]) <= max_radius and abs(adj_loc[1] - start_loc[1]) <= max_radius:
        dx, dy = spiral_dir.get_dx_dy()
        adj_loc = (adj_loc[0] + dx, adj_loc[1] + dy)
        cur_segment_len += 1
        if _is_traversable_loc(adj_loc, state):
            target_loc, target_dir = _find_unoccupied_adj_loc(adj_loc, state, agent_loc)
            if target_loc is not None:
                action, action_kwargs = _move_adj_to_loc(target_loc, state, agent)
                if not 'success' in action_kwargs or action_kwargs['success'] == True:
                    return adj_loc

        if cur_segment_len >= max_segment_len:
            spiral_dir = Direction.counterwise(spiral_dir)
            cur_segment_len = 0
            dx, dy = spiral_dir.get_dx_dy()
            if dy == 0:
                max_segment_len += 1
    
    print("No suitable traversable location was found in radius")
    return None

def _find_item_drop_loc_near_loc(agent, start_loc, state, max_radius=3, require_counter=False):
    
    ag = state[agent.agent_id]
    agent_loc = ag['location']

    # Spiral outwards towards a drop loation
    spiral_dir = Direction.East()
    adj_loc = start_loc
    max_segment_len = 1
    cur_segment_len = 0
    while abs(adj_loc[0] - start_loc[0]) <= max_radius and abs(adj_loc[1] - start_loc[1]) <= max_radius:
        dx, dy = spiral_dir.get_dx_dy()
        adj_loc = (adj_loc[0] + dx, adj_loc[1] + dy)
        cur_segment_len += 1
        if _is_suitable_drop_loc(adj_loc, state, require_counter):
            target_loc, target_dir = _find_unoccupied_adj_loc(adj_loc, state, agent_loc)
            if target_loc is not None:
                action, action_kwargs = _move_adj_to_loc(target_loc, state, agent)
                if not 'success' in action_kwargs or action_kwargs['success'] == True:
                    return adj_loc

        if cur_segment_len >= max_segment_len:
            spiral_dir = Direction.counterwise(spiral_dir)
            cur_segment_len = 0
            dx, dy = spiral_dir.get_dx_dy()
            if dy == 0:
                max_segment_len += 1
    
    print("No suitable drop location was found in radius")
    return None

def _distance(loc_a, loc_b):
    return max(abs(loc_a[0] - loc_b[0]), abs(loc_a[1] - loc_b[1]))

def _is_traversable_loc(location, state):
    object_ids = list(state.keys())
    for object_id in object_ids:
        obj = state[object_id]
        if 'location' in obj:
            loc = obj['location']
            if loc[0] is location[0] and loc[1] is location[1]:
                if 'is_traversable' in obj and obj['is_traversable']:
                    return True
    return False

def _is_suitable_drop_loc(location, state, require_counter=False):
    object_ids = list(state.keys())
    counter = False
    
    for object_id in object_ids:
        obj = state[object_id]
        if 'location' in obj:
            loc = obj['location']
            if loc[0] is location[0] and loc[1] is location[1]:
                #is_traversable = 'is_traversable' in obj and obj['is_traversable']
                has_stack = 'stack' in obj and obj['stack']
                is_usable = 'is_usable' in obj and obj['is_usable']
                is_counter = 'is_counter' in obj and obj['is_counter']
                is_source = 'is_source' in obj and obj['is_source']
                if is_counter:
                    counter = True
                if has_stack or is_usable or is_source:
                    return False
    
    return (not require_counter) or counter
            

def _find_unoccupied_adj_loc(location, state, agent_location=None):
    object_ids = list(state.keys())
    
    directions = [Direction.North(), Direction.East(), Direction.South(), Direction.West()]

    # first check if the agent is not already adjacent
    if agent_location is not None:
        for d in directions:
            dx, dy = d.get_dx_dy()
            adj_loc = (location[0] + dx, location[1] + dy)
            if adj_loc == agent_location:
                return adj_loc, Direction.inverse(d)

    # otherwise pick the first available spot
    for d in directions:
        dx, dy = d.get_dx_dy()
        adj_loc = (location[0] + dx, location[1] + dy)
        traversable = True
        
        for object_id in object_ids:
            if 'location' in state[object_id]:
                loc = state[object_id]['location']
                if loc[0] is adj_loc[0] and loc[1] is adj_loc[1]:
                    if (not 'is_traversable' in state[object_id]) or (not state[object_id]['is_traversable']):
                        traversable = False
                        break  
        if traversable:
            return adj_loc, Direction.inverse(d)
    
    return None, None

"""
TODO:
    some way to determine the most efficient route of tasks. a planner of sorts.
    simplest thing to do is to decompose all possible subtasks, and take the action of the most shallow tree
"""
def _perform_subtasks(subtasks, state, ai_cook, args=(None, {'depth':0}), ignore_mark=True, whitelist=[], max_depth=float('inf'), ignore_whitelist=False):
          
    if not 'depth' in args[1]:
        args[1]['depth'] = 0
        
    if args[1]['depth'] > max_depth:
        print("No whitelisted subtasks to complete at this depth")
        return args
    
    
    for subt_a, subt_b in subtasks:

        found_a = _find_itemstack_in_state(subt_a, state, ignore_source=False, ignore_mark=ignore_mark)
        hold_a = _is_holding_itemstack(ai_cook, subt_a, state, ignore_mark=ignore_mark)

        
        # If the agent is not allowed to produce this item, let it further decompose the task
        if not ignore_whitelist and (whitelist and (subt_a not in whitelist)):
            found_a, hold_a = None, False
            
        # If subtask a is not completed, go complete it
        if found_a is None and not hold_a:
            subs = subt_a.get_subtasks()
            if subs:
                args[1]['depth'] += 1
          
                # if we have a whitelist and are allowed to do this action, allow one step below that action
                action, action_args = _perform_subtasks(subs, state, ai_cook, args=args, whitelist=whitelist, max_depth=max_depth, ignore_whitelist=(whitelist and subt_a in whitelist))
                if action is not None:
                    return action, action_args
                
         # If subtask b is a recipe, assemble and fetch it     
        if isinstance(subt_b, Recipe):
            #hold_b = _is_holding_itemstack(ai_cook, subt_b, state)              
            found_b = _find_itemstack_in_state(subt_b, state, ignore_source=False)
            found_b_not_source = _find_itemstack_in_state(subt_b, state, ignore_source=True)
            
            # If the agent is not allowed to produce this item, let it further decompose the task
            if not ignore_whitelist and (whitelist and (subt_b not in whitelist)):
                found_b, found_b_not_source = None, None  
                
            # If we cannot find subtask b, decompose it to a simpler task
            if found_b is None:
                subs = subt_b.get_subtasks()
                if subs:
                    args[1]['depth'] += 1
                    
                    # if we have a whitelist and are allowed to do this action, allow one step below that action:
                    action, action_args = _perform_subtasks(subs, state, ai_cook, args=args, whitelist=whitelist, max_depth=max_depth, ignore_whitelist=(whitelist and subt_b in whitelist))
                    if action is not None:
                        return action, action_args
            
            # If we are holding a and b exists (and is not a source)
            if hold_a and found_b_not_source is not None:
                print("Go merge hold item a with existing item ", found_b)
                return _put_itemstack_in_state(ai_cook, state[found_b_not_source]['location'], state, args)
            
            # If we are not holding a and b exists (and is not a source)
            if found_a is not None and not hold_a and found_b_not_source is not None:
                print("Go fetch item", found_a)
                return _fetch_itemstack_in_state(ai_cook, found_a, state, args)
           
            
           
        # If subtask b is not a recipe, we have processing of task a to do
        elif (found_a is not None or hold_a) and (not isinstance(subt_b, Recipe)):
            use_id = _find_usable_in_state(state, subt_b)

            if use_id is not None:
                use_loc = state[use_id]['location']
                agent_loc = state[ai_cook.agent_id]['location']
                
                # find if the object is already at location
                a_at_loc = _is_itemstack_at_location(subt_a, use_loc, state)
                
                # If we are holding something that is not a, drop it
                if not hold_a and state[ai_cook.agent_id]['is_carrying']:
                    drop_loc = _find_item_drop_loc_near_agent(ai_cook, state, max_radius=3, require_counter=True)    
                    if drop_loc is not None:            
                        print("Go drop item")
                        return _put_itemstack_in_state(ai_cook, drop_loc, state, args)
                    return args
                
                # find if the processing location is occupied (by anything)
                occ_id = _find_itemstack_at(use_loc, state)
                if not a_at_loc and occ_id is not None:
                   print('Clearing the use location')
                   return _fetch_itemstack_in_state(ai_cook, occ_id, state, args)
               
                # if a is not yet at the processing location and we are holding it
                if not a_at_loc and hold_a:
                    print("Bringing item", found_a ," to processing location", use_id)
                    return _put_itemstack_in_state(ai_cook, use_loc, state, args)
                
                # if a is at the processing location but the agent is not
                agent_dir = state[ai_cook.agent_id]['direction']
                dx, dy = Direction.from_name(agent_dir).get_dx_dy()
                agent_facing = (agent_loc[0] + dx, agent_loc[1] + dy)
                if a_at_loc and (use_loc[0] != agent_facing[0] or use_loc[1] != agent_facing[1]):
                    print("Move to processing location item", found_a)
                    return _move_adj_to_loc(use_loc, state, ai_cook, args)
                
                # If a is at the location and the agent is too
                if a_at_loc and (use_loc[0] == agent_facing[0] and use_loc[1] == agent_facing[1]):
                    print("Processing item ", found_a)
                    return _use_action(ai_cook, state, args)
    
                # if a is not yet at the processing location and we are not holding it
                if not a_at_loc and not hold_a:
                    print("Go fetch item", found_a)
                    return _fetch_itemstack_in_state(ai_cook, found_a, state, args)
                
            else:
                print("Cannot find tool to process item", found_a) 
        
    return args