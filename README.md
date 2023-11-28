# Matrx Overcooked

## Description
Python implementation of the "Overcooked!" video game in Matrx for scientific participant studies into Human Machine Teaming (insert paper reference here).

## Features
 - Supports multiple human and artificial agents working together.
 - Supports large but simple kitchen worlds
 - Supports kitchen actions of different lengths
 - Supports an unlimited number of recipes of varying complexity
 
## Installation
Python 3 must be installed. Please view the requirements.txt for required python packages. We recommend using a virtual environment (venv) to install all the packages in one go. After you have created your venv, update the 'run.bat' file to point to the 'python.exe' file in your venv installation.

## First use
- We recommend to first run through the included default scenario. You can do this using the included 'run.bat' file or by running `python main.py` in the root directory.
- You will be prompted to enter a participant number. The default setup supports participant numbers 1 through 61 (you can find these in 'conditions.csv').
- You can then go to  'http://localhost:3000/human-agent/agent_(you)#' in your browser to partake in the experiment.
- When the experiment is done, you will find the recorded simulation data per trial in the 'logs' folder (stored in the folder of the participant number you entered).

## Configuring the setup
The Overcooked environment is entirely configurable. Some features require basic knowledge of Python and Matrx, others are simple json files.

### Changing conditions and participant numbers
The 'conditions.csv' file in the root directroy maps participant numbers to condition numbers. The default setup has 6 conditions. When the simulation boots, it will search for level configuration files in '/levels/condition_x/', where 'x' is the participant's condition number.

### Changing levels
The 'levels.json' file in the root directory is a simple list of the levels that will be run with main.py. These are filenames that must be present in the each '/levels/condition_x/' folder. Each of these configuration files includes a variety of configurable properties of a trial:
- "agents". Include any number of human or artificial agents here. The current python implementation only supports 1 human and 1 artificial agent; but this can easily be expanded with some python and javascript knowledge. Note that the 'agent_id' controls the image that will be used for the agent; matching .gif and .png files must be present in the '/matrix_env/images/agents/' folder.
- "recipes". This determines all the dishes that can be created. You can change, for example, what toppings go on a salad, as well as a minimum and maximum number of toppings. Custom recipes will be explained further down.
- "goals". This is a list of the orders that will appear. For each order, you can specify what ingredients it should have, after how many ticks it should appear, and how many ticks participants have to finish the order. Make sure the orders in goals can be created using the recipe families in "recipes"!. 
- "welcome_text". This text will be displayed with a 'start' button before the participants start this level.
- "final_text". This text will be displayed with a 'continue' button after the participant has completed this level.

### Custom recipes
Some example recipes are included in the '/matrix_env/recipes/' folder. The python scripts will generate a lot of images for you at run time, but make sure that your fresh ingredients and processed ingredients are in the '/matrx_env/images/ingredients/' folder. 
- Each recipe family has a family id. All recipes generated from this family are considered part of that family.If an ingredient should look different for a different recipe family (say for example, tomato slices on a 'burger'), include these variations in the appropriate folder (e.g. 'images/ingredients/burger')
- Each recipe family has a list of base ingredients. These are used to determine to which recipe family a stack of ingredients belong (e.g. a stack with lettuce is assumed to belong to the 'salad' family).
- Each recipe family has a list toppings. You can specify how many of these are required for a dish to qualify as a recipe of this family, and how many it should accept at most.
- The default version uses only the 'Chopped(ingredient_name)' predicate. 'Cooked' and 'Grilled' are also recognised, but not mapped to a tool currently (like how 'Chopped' is mapped to the Cutting Board object). This can be added, but will require some python knowledge.

### Custom kitchen layouts
The layout and game rules for the default setup can be found in  '/matrx_env/cases.py'. With some python knowledge, these can be adapted or changed. Of special note here is the `ToolMap` dictionary in `OvercookedCase`, which can be used to map predicates to game objects.

### Custom agent behaviour
All the behaviour for the human and artificial agents can be found in '/matrx_env/cooks.py'. With some python knowledge, this can be adapted or changed.
All the Matrx actions used by the agents can be found in '/matrx_env/actions.py'. With some python knowledge, these can be adapted or changed.

### Custom game objects
All the objects in the game (like the cutting board) can be found in '/matrx_env/objects.py'. With some python knowledge, these can be adapted or changed.
- Game objects can be very simple. For an example of more advanced behaviour, look at the `CuttingBoard` class

## Authors and acknowledgment
All authorship of this repository belongs with TNO.

## License
This repository is released under the MIT license that is also used by the Matrx project itself.
