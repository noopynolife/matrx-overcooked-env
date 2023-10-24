# -*- coding: utf-8 -*-
"""
Created on Tue May 23 13:28:09 2023

@author: cornelissennaj
"""
import os, sys, shutil, json, datetime
root_path = os.path.dirname(os.path.abspath("root"))
sys.path.append(str(root_path))

import pandas as pd

from matrx_visualizer import visualization_server
from matrx.logger import GridWorldLogger
from matrx.logger.log_agent_actions import LogActionsV2
from matrx.logger.log_idle_agents import LogIdleAgentsV2
from matrx.logger.log_messages import MessageLoggerV2
from matrx.logger.log_tick import  LogDurationV2
from matrx.api import api

from overcooked_env.cases import OvercookedCase

if __name__ == "__main__":

    # Get the media folder
    media_folder = os.path.join(os.path.realpath("overcooked_env"), "images")
    temp_folder = media_folder+"\\temp"
    log_folder = os.path.join(os.path.realpath(""), "logs")
    
    # Cleanup the temp folder
    #shutil.rmtree(temp_folder, ignore_errors=False, onerror=None)
     # Create a temp folder in the media folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
        
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)     
        
    
    # Ask the researcher to input the correct participant identifier
    print("Welcome to the Overcooked Simulation for Meaningful Human Control.")
    
    condition = None
    while(condition == None):
        print("Please enter the participant number and press 'Enter':")
        participant_number = input()
        participant_folder = log_folder+"\\"+str(participant_number)
        if not os.path.exists(participant_folder): 
            os.makedirs(participant_folder)
        
        try:
            conditions = pd.read_csv("conditions.csv", sep=";")
            df = conditions[conditions['participant_number']==int(participant_number)]
            if len(df) > 0:
                condition = df.iloc[0].condition_nr
            else:
                print("Could not find condition number for the entered participant number.")
                print()
        except Exception as e:
            print("The participant number must be an integer.")
            
    boot_time = str(datetime.datetime.now()).rsplit(".")[0].replace(":", "-")
    session_folder = participant_folder + "\\" + boot_time
    if not os.path.exists(session_folder): 
        os.makedirs(session_folder)
    print("Succesfully created folder: "+session_folder+"\\")
    print("")
    print("Now booting Matrx..")
    print("")
    print("")
    
    api_info = {"run_matrx_api": True}

    # Start the MATRX API we need for our visualisation
    api_info['api_thread'] = api._run_api(verbose=False)
    
    # Start the custom visualization Thread
    api_info['vis_thread'] = visualization_server.run_matrx_visualizer(verbose=False, media_folder=media_folder)
    

    # Open our file of levels
    f = open("levels.json", "r")
    levels = json.loads(f.read())['levels']
    f.close()

    for ses_id, level in enumerate(levels):
    
        # Call our method that creates our builder
        builder = OvercookedCase(LevelFile="levels\\condition_"+str(condition)+"\\"+level, KitchenSize=[9, 9]).create_builder(verbose=False)
        
        # Add our loggers
        builder.add_logger(LogActionsV2, log_strategy=GridWorldLogger.LOG_ON_GOAL_REACHED, save_path=session_folder+"\\trial_"+str(ses_id), file_name_prefix="actions")
        builder.add_logger(LogIdleAgentsV2, log_strategy=GridWorldLogger.LOG_ON_GOAL_REACHED, save_path=session_folder+"\\trial_"+str(ses_id), file_name_prefix="idleagents")
        builder.add_logger(LogDurationV2, log_strategy=GridWorldLogger.LOG_ON_GOAL_REACHED, save_path=session_folder+"\\trial_"+str(ses_id), file_name_prefix="duration")
        builder.add_logger(MessageLoggerV2, log_strategy=GridWorldLogger.LOG_ON_GOAL_REACHED, save_path=session_folder+"\\trial_"+str(ses_id), file_name_prefix="messages")

        # run the world
        world = builder.get_world()
        world.run(api_info)
