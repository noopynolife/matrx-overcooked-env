# Matrx Overcooked

## Name
Python implementation of the "Overcooked!" video game in Matrx for scientific participant studies

## Description
<todo>

## Roadmap

### ItemStack
- [x] Finish Take() method
    - [x] Make EnvObject implement take() by changing all instances of itemStack in actions.py and cooks.py into stack
    - [x] Make ItemStacks 'carried_by' on Take
    - [x] Move ItemStacks location to agent on Take
	- [x] Reset carried_by if item was unsuccesfully removed
	- [x] Update avater icon with the held itemStack
- [x] Implement Put() for ItemStacks
- [x] Directionality of agents would be good
- [x] Let agents pick up and put away only items in front of them

### Recipe Book
- [x] Add a configurable recipe book
- [x] Should contain rules for what items do and don't stack, swap if otherwise
- [x] Should contain rules for merging items (e.g. ['Lettuce_Chopped', 'Tomato_Chopped'] -> ['Salad'])
- [x] Should contain rules for processing items (e.g. CuttingBoard(['Lettuce_Fresh']) -> ['Lettuce_Chopped'], time=2s)

### Useables
- [x] Add use() to all usables.
- [x] Useables should have an action animation / bar
- [x] Sometimes using a useable can fail

### Level configuration
- [x] Incoming orders
- [x] Save as json file (level.json)
- [x] Should contain recipe family
- [x] Include events (e.g. agent reliability)
- [x] Add final 'world goal' that finishes after the timer runs out or if the last task is completed

### General Interface
- [x] Add timer
- [x] Add score
- [x] Add message on level finish
- [x] Add order queue
- [ ] Add recipe book
- [x] Add delegation interfaces
    - [x] taskbased
		- [x] be able to delegate tasks
		- [x] see current task(s)
		- [x] be able to cancel current tasks
	- [x] playbased
		- [x] be able to initiate a different play
		- [x] see current play
    - [x] goalbased
		- [x] be able to assign a different priority
		- [x] see current priority

### AgentBrains
- [x] We assume agents were designed and calibrated for their use. i.e. they know the initial state of the kitchen, they know the initial recipes.
- [x] Add reliability tracker
- [x] Add task based agent
    - [x] pathfinding
    - [x] basic task decomposition
	- [ ] improve object interaction behaviour
	- [ ] add 'back off' task
- [ ] Add playbased agent
    - [x] pathfinding
    - [x] advanced task decomposition
    - [x] implement plays
	- [ ] goal order prioritizing
	- [x] add 'none' play 
	- [ ] improve idle behaviour
	- [ ] improve recipe optimizations
	- [ ] improve closest-object finding
- [ ] Add goal based agent
    - [x] pathfinding
    - [x] complete task decomposition
	- [x] agent priorities
    - [ ] goal order prioritizing
	- [x] priorities should influence reliability
	- [ ] priorities should influence reliability
	- [x] add 'none' goal
	- [ ] improve idle behaviour
	- [ ] improve recipe optimizations
	- [ ] improve closest-object finding

### Introductory material participants
- [x] Introductory level without teammate
- [x] Introductory level playbased
- [x] Introductory level taskbased
- [x] Introductory level goalbased 

### Actual participant levels
- [ ] Add metrics with matrx logger
- [x] Design final kitchen layout / task specification
- [ ] Tweak final parameters
- [x] Develop 3 aesthetics each for different agent reliabilities

### Agent controls
- [x] Mouse
- [ ] Keyboard (WASD + arrow keys)

## Authors and acknowledgment
<todo>

## License
<todo>
