# -*- coding: utf-8 -*-
"""
Created on Tue May 30 14:22:49 2023

@author: cornelissennaj
"""

from matrx import WorldBuilder

from .objects import TableTop, ItemStack, CuttingBoard, SourceTop, DeliveryTop, TrashTop
from .cooks import AgentType, HumanCookBrain, TaskBasedCookBrain, GoalBasedCookBrain, PlayBasedCookBrain
from .controls import WASD, ARROWS, IJKL
from .util import Direction
from .ingredients import Plate, Tomato, Onion, Lettuce
from .recipes import RecipeBook
from .predicates import Merged, Chopped, Cooked, Grilled, Deliverable
from .tasks import Task, TaskType, TaskId, GoalBook
from .liabilities import Reliability

import json
import numpy as np

def create_objects_outer_square(name, bottom_right, top_left=(0,0)):
    objects_xy, objects_name = [], []
    for i in range(top_left[0], bottom_right[0]):
        objects_xy.append([i, int(top_left[1])])
        objects_xy.append([i, int(bottom_right[1]-1)])
        objects_name.append(name+"_"+str(i)+"_"+str(top_left[0]))
        objects_name.append(name+"_"+str(i)+"_"+str(bottom_right[1]-1))
    for j in range(top_left[1]+1, bottom_right[1]-1):
        objects_xy.append([int(top_left[1]), j])
        objects_xy.append([int(bottom_right[0]-1), j])
        objects_name.append(name+"_"+str(top_left[1])+"_"+str(j))
        objects_name.append(name+"_"+str(bottom_right[0]-1)+"_"+str(j))
    return objects_xy, objects_name



class OvercookedCase():

    BackgroundColor = "#C6C6C6"
    KitchenWallColor = "#161616"
    KitchenFloorColor = "#F5E6D2"
    TableTopColor = "#DCAA6E"
    InitDirection = Direction.South()
    ToolMap = { ItemStack : Merged.name,
                CuttingBoard : Chopped.name,
                DeliveryTop : Deliverable.name }

    def __init__(self, LevelFile, KitchenSize=[11,11], BackgroundColor=None, KitchenWallColor=None, KitchenFloorColor=None, TableTopColor=None, ToolMap=None):
        assert LevelFile != "", "Cannot build an overcooked case without a level file" 
        self.LevelFile = LevelFile
        self.KitchenSize = np.array(KitchenSize, dtype=int)

        if BackgroundColor is not None:
            self.BackgroundColor = BackgroundColor
        if KitchenWallColor is not None:
            self.KitchenWallColor = KitchenWallColor
        if KitchenFloorColor is not None:
            self.KitchenFloorColor = KitchenFloorColor
        if TableTopColor is not None:
            self.TableTopColor = TableTopColor
        if ToolMap is not None:
            self.ToolMap = ToolMap
    
    
    def create_builder(self, verbose=False):
        # Load the level data
        f = open(self.LevelFile, "r")
        level = json.loads(f.read())['level']
        f.close()
    
        # Load the recipes
        recipeBook = RecipeBook.from_json_object(level)
        recipeBook.register_recipes(self.ToolMap, overwrite=True)

        # Create our builder
        builder = WorldBuilder(shape=[int(self.KitchenSize[0]), int(self.KitchenSize[1])], 
                               run_matrx_api=True, 
                               run_matrx_visualizer=False,
                               visualization_bg_clr=self.BackgroundColor, 
                               tick_duration=0.2, verbose=verbose)
        
        move_tasks = []
        for agent in level['agents']:
            if agent['agent_type'] == AgentType.HUMAN:
                move_to = self.add_agent(agent, builder, recipeBook)
                #move_tasks.append(move_to)
            else:
                self.add_agent(agent, builder, recipeBook, move_tasks)
                          
                
        # Preload the images
        agent_base_imgs = ["agents\\"+agent['agent_id']+".gif" for agent in level['agents']]
        recipeBook.preload_agent_images(agent_basefiles=agent_base_imgs)    
    
    
        # Load the goals
        goalBook = GoalBook.from_json_object(level)
        goalBook.register_goals_to_world(builder, overwrite=True)
        goalBook.register_goals_to_tool(DeliveryTop, overwrite=True)
        
        DeliveryTop.WELCOME = level['welcome_text']
        DeliveryTop.GOODBYE = level['final_text']
        
        # Add the kitchen floor
        builder.add_room(top_left_location=[0, 0], name="Kitchen",
                         width=self.KitchenSize[0], height=self.KitchenSize[1], 
                         area_visualize_colour=self.KitchenFloorColor,
                         with_area_tiles=True, wall_visualize_opacity=0.4)
        
        # Add the tabletops surrounding the kitchen
        #tabletops_xy, tabletops_name = create_objects_outer_square("TableTop", self.KitchenSize-1, [1,1])
        tabletops_xy = [[3,4], [4,4]]  # we add the middle tables first so the artificial agent finds them first in search
        tabletops_xy.extend([[1,1], [2,1], [3,1], [5,1], [6,1], [7,1], [1,2], [1,4], [1,6], [1,7], [2, 7], [4, 1], [4,7], [7, 7], [7, 6], [7, 3], [7, 2]])
        tabletops_name = ["TableTop_"+str(x[0])+"_"+str(x[1]) for x in tabletops_xy]
        for idx in range(len(tabletops_xy)):
            builder.add_object(location=tabletops_xy[idx], 
                               name=tabletops_name[idx],
                               callable_class=TableTop)
        
        # Add a source box for onions
        builder.add_object(location=[6,7],
                           name="Source_Onion",
                           callable_class=SourceTop,
                           source_stack=Onion())
        
         # Add a source box for tomato
        builder.add_object(location=[5,7],
                           name="Source_Tomato",
                           callable_class=SourceTop,
                           source_stack=Tomato())
        
        # Add a source box for lettuce
        builder.add_object(location=[3,7],
                           name="Source_Lettuce",
                           callable_class=SourceTop,
                           source_stack=Lettuce())
        
        # Add a tabletop with cutting board
        builder.add_object(location=[7,5],
                         name="TableTop_Cutboard_4",
                         callable_class=CuttingBoard,
                         use_type=self.ToolMap[CuttingBoard])
        
        # Add a source box for plate
        #builder.add_object(location=[4,1],
        #                   name="Source_Plate",
        #                   callable_class=SourceTop,
        #                   source_stack=Plate())
        
        # Add a tabletop with cutting board
        builder.add_object(location=[7,4], 
                         name="TableTop_Cutboard_5",
                         callable_class=CuttingBoard,
                         use_type=self.ToolMap[CuttingBoard])
        
        # Add the delivery place
        builder.add_object(location=[1,3], 
                         name="Source_Deli",
                         callable_class=DeliveryTop)
        
        # Add a trash bin
        builder.add_object(location=[1,5], 
                         name="Trash_bin",
                         callable_class=TrashTop)

        # Return the builder
        return builder
        
    def add_agent(self, agent, builder, recipeBook, move_tasks=[]):
        agent_type = agent['agent_type']
        agent_id = agent['agent_id']
        agent_name = agent['agent_name']
        
        if agent_type == AgentType.HUMAN:
            # Add a human controllable agent with certain controls and a GIF
            human_brain = HumanCookBrain(direction=self.InitDirection)
            move_to_human = Task(TaskType.MOVE, agent_id, agent_name, "agents\\"+agent_id+"_south.png")
            reliability = Reliability.from_json_object(agent)
            recipeBook.add_flawed_recipes(reliability.liabilities)
    
            builder.add_human_agent(location=[3, 3], 
                                    agent_brain=human_brain, 
                                    name=agent_name,
                                    team="team_1",
                                    key_action_map={**WASD, **ARROWS}, 
                                    img_name=self.InitDirection.directional_img("agents\\"+agent_id+".gif"),
                                    direction=self.InitDirection.name, 
                                    search_name=agent_id, 
                                    display_name=agent_name,
                                    reliability=reliability)
            return move_to_human
            
        if agent_type == AgentType.TASK_BASED:
            """
            Initialize a task based agent
            """
            move_tasks += [DeliveryTop([7,2]).get_as_task('move'), 
                          CuttingBoard([2,7]).get_as_task('move'), 
                          TableTop([1,1]).get_as_task('move'),
                          TrashTop([5, 2]).get_as_task('move')]
            chopTask = Task(TaskType.USE, TaskId.CHOP, "Chop", "icons\\chop.png")
            use_tasks = [chopTask]
            ai_brain = TaskBasedCookBrain(recipeBook, move_speed=10.0, direction=self.InitDirection)
            reliability = Reliability.from_json_object(agent)
            recipeBook.add_flawed_recipes(reliability.liabilities)
        
            builder.add_agent(location=[4, 3], 
                              agent_brain=ai_brain, 
                              name=agent_name, 
                              team="team_1",
                              is_traversable=False,
                              img_name=self.InitDirection.directional_img("agents\\"+agent_id+".gif"), 
                              direction=self.InitDirection.name, 
                              recipeBook=recipeBook, 
                              queued_tasks=[], 
                              completed_tasks=[],
                              move_tasks=move_tasks, 
                              use_tasks=use_tasks,
                              reliability=reliability)
        
        if agent_type == AgentType.GOAL_BASED:
            """
            Initialize a goal based agent
            """
            noPriority = Task(TaskType.GOAL, TaskId.NONE, "None", "icons\\no_action.png")
            speedPriority = Task(TaskType.GOAL, TaskId.PRIO_SPEED, "Speed", "icons\\prio_speed.png")
            safetyPriority = Task(TaskType.GOAL, TaskId.PRIO_SAFETY, "Safety", "icons\\prio_safety.png")
            qualityPriority = Task(TaskType.GOAL, TaskId.PRIO_QUALITY, "Quality", "icons\\prio_quality.png")
            priority_tasks = [noPriority, speedPriority, safetyPriority, qualityPriority]
            ai_brain = GoalBasedCookBrain(recipeBook, move_speed=10.0, direction=self.InitDirection)        
            reliability = Reliability.from_json_object(agent)
            recipeBook.add_flawed_recipes(reliability.liabilities)
    
            builder.add_agent(location=[4, 3], 
                              agent_brain=ai_brain, 
                              name=agent_name, 
                              team="team_1",
                              is_traversable=False,
                              img_name=self.InitDirection.directional_img("agents\\"+agent_id+".gif"), 
                              direction=self.InitDirection.name, 
                              recipeBook=recipeBook, 
                              queued_tasks=[], 
                              completed_tasks=[],
                              priority_tasks=priority_tasks,
                              active_priorities=[TaskId.NONE],
                              reliability=reliability)
        
        if agent_type == AgentType.PLAY_BASED:
            """
            Initialize a play based agent
            """
            noPlay = Task(TaskType.PLAY, TaskId.NONE, "None", "icons\\no_action.png")
            assemblePlay = Task(TaskType.PLAY, TaskId.PLAY_ASSEMBLE, "Assemble Dishes", "icons\\play_assemble.png")
            vegetablePlay = Task(TaskType.PLAY, TaskId.PLAY_VEG, "Prepare Vegetables", "icons\\play_vegetables.png")
            servePlay = Task(TaskType.PLAY, TaskId.PLAY_SERVE, "Serve Dishes", "icons\\play_serve.png")
            play_tasks = [noPlay, assemblePlay, vegetablePlay, servePlay]
            ai_brain = PlayBasedCookBrain(recipeBook, move_speed=10.0, direction=self.InitDirection)        
            reliability = Reliability.from_json_object(agent)
            recipeBook.add_flawed_recipes(reliability.liabilities)
    
            builder.add_agent(location=[4, 3], 
                              agent_brain=ai_brain, 
                              name=agent_name, 
                              team="team_1",
                              is_traversable=False,
                              img_name=self.InitDirection.directional_img("agents\\"+agent_id+".gif"), 
                              direction=self.InitDirection.name, 
                              recipeBook=recipeBook, 
                              queued_tasks=[], 
                              completed_tasks=[],
                              play_tasks=play_tasks,
                              action_whitelist=[],
                              active_plays=[TaskId.NONE],
                              reliability=reliability)