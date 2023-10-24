$(".nav-link").click( function() {
	  $(this).parent().parent().children(".nav-item").each(function () {
			$(this).children(".nav-link").each(function (){
				$(this).removeClass("active");
				});
			});
	  $(this).addClass("active");
 });

function update_timer(end_time, world_settings){
	current_tick = world_settings['nr_ticks'];
	tick_duration = world_settings['tick_duration'];
	time_left = (end_time - current_tick) * tick_duration;
	minutes_left = Math.floor(time_left / 60);
	seconds_left = Math.floor(time_left % 60);
	
	
	timer_span = document.getElementById("timer");
	timer_span.innerHTML = minutes_left.toString().padStart(2, '0') + ":" + seconds_left.toString().padStart(2, '0');
}

function update_scoreboard(score){
	score_span = document.getElementById("scoreboard");
	score_span.innerHTML = score;
}

function show_loading_screen(){
	loading = document.getElementById("loading");
	if (loading.style.display !== "flex" ){
		loading.style.display = "flex";
	}
}

function show_start_menu(){
	
	start_menu = document.getElementById("start_menu");
	if (start_menu.style.display !== "flex" ){
		start_menu.style.display = "flex";
	}
}

function show_end_simulation(score){
	finished_menu = document.getElementById("finished_menu");
	if (finished_menu.style.display !== "flex" ){
		final_score_span = document.getElementById("final_score");
		final_score_span.innerHTML = score;
		finished_menu.style.display = "flex";
	}
}

function hide_end_simulation(){
	finished_menu = document.getElementById("finished_menu");
	finished_menu.style.display = "none";
}

function hide_loading_screen(){
	loading = document.getElementById("loading");
	loading.style.display = "none";
}

function hide_start_menu(){
	start_menu = document.getElementById("start_menu");
	start_menu.style.display = "none";
}


function update_cover_screen(){
	cover_screen = document.getElementById("cover_screen").style;
	
	finished_menu = document.getElementById("finished_menu").style;
	loading = document.getElementById("loading").style;
	start_menu = document.getElementById("start_menu").style;

	if (finished_menu.display === 'none' && loading.display === 'none' && start_menu.display === 'none'){
		if (cover_screen.visibility !== 'hidden'){
			cover_screen.visibility = "hidden";
		}
	}else {
		if (cover_screen.visibility !== 'visible'){
			cover_screen.visibility = "visible";
		}
	}
}

/*
Send this message to the AI agent when the human agent presses a task button
*/
function delegate(action, target) {
	msg = "";
	if (action === 'play'){
		msg = "Start " + action + " labeled " + target + ".";
	}
	else if (action === 'priority'){
		msg = "Shift " + action + " to " + target + ".";
	}
	else if (action === 'move'){
		msg = "Please " + action + " to " + target + ".";
	}
	else{
		msg = "Please " + action + " a " + target + ".";
	}
    data = {"content": msg, "sender": lv_agent_id, "receiver": null}; // setting receiver to null sends the message to all agents
    send_matrx_api_post_message(matrx_send_message_url, data);
}

var cancelled = [];
/*
Send this message to the AI agent when the human agent presses a task button
*/
function cancel_task(target_id) {
	msg = "Please cancel task " + target_id + ".";
    data = {"content": msg, "sender": lv_agent_id, "receiver": null, "action": 'cancel', "target": target_id}; // setting receiver to null sends the message to all agents
    send_matrx_api_post_message(matrx_send_message_url, data);
	cancelled.push(target_id);
}

/*
Unpacks dict values into one array. Does NOT preserve dict keys.
*/
function unpack_tool_tasks(dictionary){
	arr = [];
    for(var key in dictionary){
		tool = dictionary[key];
		for (var k in tool){
			arr = arr.concat(tool[k]);
		}
    }
	return arr;
}

/*
Generate all the buttons in a button group (buttons in the same group should share the same task type
*/
function populate_group(tasks, group_name, task_type){
	button_group = document.getElementById(group_name);
	for (var i = 0; i < tasks.length; i++){
		task = tasks[i];
		btn = create_button_delegate(task, task_type);
		button_group.appendChild(btn);
	}
	submenu = button_group.parentNode.parentNode;
	searchbox = submenu.children[1].children[1];
	search(searchbox); //perform a search to order all the items
}

/*
Highlight any buttons in a group that match the given name
*/
function highlight_button_in_group(group_name, button_names, added_text=""){
	button_group = document.getElementById(group_name);
	idx = -1; // use negative values to show the active plays up front (always)
	
	for (var i = 0; i < button_group.children.length; i++){
		btn = button_group.children[i];
		if (  button_names.includes(btn.getAttribute('unique_name'))  ){
			if (btn.style.order >= 0){
				btn.style.backgroundColor = 'green';
				btn.style.borderColor = 'green';
				btn.children[1].innerHTML += added_text;
				btn.style.order = idx;
				idx -= 1; //display this item up front
			}
		}else{
			if (btn.style.order < 0){
				btn.style.removeProperty( 'background-color' );
				btn.style.removeProperty( 'border-color' );
				btn.children[1].innerHTML = btn.children[1].innerHTML.slice(0, -added_text.length);
				btn.style.order = 0; //wait for the next search to re-order this item
			}
		}
	}
}

/*
Generate all the 'goal' divs
*/
function repopulate_goals(goals, current_tick){
	goal_group = document.getElementById("goals");

	// If there is no goals, don't display any divs
	if (goals.length === 0){
		goal_group.textContent = '';
	}else{
		for (var i = 0; i < goals.length; i++){	

			goal_mk = goals[i]['target']['mark'];
				
			// IF the th div does not match with the ith goal, remove it
			while (goal_group.children.length > i && goal_group.children[i].getAttribute('mark') !== goal_mk){
				goal_group.removeChild(goal_group.children[i]);
			}
				
			//Then if they DO match, update the timer bar
			if (i < goal_group.children.length){
				bar = goal_group.children[i].children[2];

				if (current_tick < goals[i]['max_nr_ticks']){
					percent =  100 - (  (current_tick-goals[i]['appears_at']) / goals[i]['expires_after'] )  * 100;
					percent_str = String( percent )+ "%";
					bar.style.width = percent_str;
					bar.style.maxWidth = percent_str;
					bar.style.minWidth = percent_str;
					if (percent < 50){
						if (percent < 15) {
							bar.style.backgroundColor = 'red';
						}
						else{
							bar.style.backgroundColor = 'orange';
						}
					}else{
						bar.style.backgroundColor = 'green';
					}
				}
				
				if (goals[i]['redo'] && goal_group.children[i].style.backgroundColor != '#FF6D6D'){
					goal_group.children[i].style.backgroundColor = '#FF6D6D';
				    goal_group.children[i].children[3].style.removeProperty( 'display' );
				}
			}
		}
	}

	// Then for the remaining goals, add them to the menu
	diff = goals.length - goal_group.children.length;
	for (var i = goals.length-diff; i < goals.length; i++){
		div = create_div_goal(goals[i]['target']);
		goal_group.appendChild(div);
	}	
}

/*
Generate all the 'task' buttons for the agent's internal task queue
*/
function repopulate_agent_tasks(tasks){
	button_group = document.getElementById("agent_tasks");

	// If there is no tasks, don't display any buttons
	if (tasks.length === 0){
		button_group.textContent = '';
	}else{
		for (var i = 0; i < tasks.length; i++){
			task_mk = tasks[i]['mark'];
			
			// IF the ith button does not match with the agent's ith task, remove it
			while (button_group.children.length > i && JSON.parse(button_group.children[i].getAttribute('mark'))[0] !== task_mk){
				remove_queued_task_button(button_group.children[i]);
			}
		}
	}
	
	// Then for the remaining tasks, add them to the menu
	total_button_tasks = 0
	for (var i = 0; i< button_group.children.length; i++){
		total_button_tasks += JSON.parse(button_group.children[i].getAttribute('mark')).length;
	}		
	diff = tasks.length - total_button_tasks;
	for (var i = tasks.length-diff; i < tasks.length; i++){	
		if (!cancelled.includes(tasks[i]['mark'])){ //don't add cancelled jobs
			add_queued_task_button(button_group, tasks[i]);
		}
	}
}

function add_queued_task_button(button_group, task){
	//IF the new task matches the last task, stack them
	if (button_group.children.length > 0){
		last = button_group.children[button_group.children.length-1];
		
		if (last.getAttribute('unique_name') === task['unique_name']){
			marks = JSON.parse(last.getAttribute('mark'));
			marks.push(task['mark']);
			marks = Array.from(new Set(marks));
			last.setAttribute('mark', JSON.stringify(marks));
			last.children[3].children[0].innerHTML = marks.length;
			if (marks.length === 2){
				last.children[3].style.removeProperty( 'display' );
			}
			return;
		}
	}
	//Otherwise add a new button
	btn = create_button_agent_task(task);
	button_group.appendChild(btn);
}

function remove_queued_task_button(btn){
	marks = JSON.parse(btn.getAttribute('mark'));
	marks.shift();
	marks = Array.from(new Set(marks));
	btn.setAttribute('mark', JSON.stringify(marks));
	if (marks.length > 0){
		btn.children[3].children[0].innerHTML = marks.length;
		if (marks.length === 1){
			btn.children[3].style.display = 'none';
		}
	}else{
		btn.parentNode.removeChild(btn);
	}
}

function create_div_goal(goal){
	img = document.createElement("img");
	img.classList.add("button-img");
	img.src = '/fetch_external_media/' +  goal['resource_name'];
	
	txt = document.createTextNode(goal['display_name']);
	span = document.createElement("span");
	span.classList.add("button-text");
	span.appendChild(txt);

	bar = document.createElement("div");
	bar.classList.add("time-bar");
	
	nbr = document.createElement("div");
	nbr.classList.add("bg-light");
	nbr.classList.add("border");
	nbr.classList.add("border-secondary");
	nbr.classList.add("number-div");
	nbr_txt = document.createTextNode("!");
	nbr_span = document.createElement("span");
	nbr_span.classList.add("number-span");
	nbr_span.style.color = 'red';
	nbr_span.appendChild(nbr_txt);
	nbr.appendChild(nbr_span);
	nbr.style.display = 'none'; //Hide this element because the new button is not a 'redo' request
	
	btn = document.createElement("div");
	btn.classList.add("btn");
	btn.classList.add("btn-light");
	btn.style.width = '33.3%';			//We want 3 buttons per row
	btn.style.maxWidth = '33.3%';
	btn.style.minWidth = '33.3%';
	btn.style.pointerEvents = 'none';
	btn.setAttribute('mark', goal['mark']);
	btn.appendChild(img);
	btn.appendChild(span);
	btn.appendChild(bar);
	btn.appendChild(nbr);

	return btn;
}

function create_button_agent_task(task){	
	img = document.createElement("img");
	img.classList.add("button-img");
	img.src = '/fetch_external_media/' +  task['resource_name'];
	
	cancel = document.createElement("img");
	cancel.classList.add("cancel-img");
	cancel.src = "/fetch_external_media/icons/cancel.png";
	
	img_holder = document.createElement("div");
	img_holder.appendChild(img);
	img_holder.appendChild(cancel);
	
	txt_type = document.createTextNode(capitalizeFirstLetter(task['task_type']));
	span_type = document.createElement("span");
	span_type.classList.add("button-text");
	span_type.appendChild(txt_type);	
	
	txt = document.createTextNode(task['display_name']);
	span = document.createElement("span");
	span.classList.add("button-text");
	span.appendChild(txt);
	
	nbr = document.createElement("div");
	nbr.classList.add("bg-light");
	nbr.classList.add("border");
	nbr.classList.add("border-secondary");
	nbr.classList.add("number-div");
	nbr_txt = document.createTextNode(task['display_name']);
	nbr_span = document.createElement("span");
	nbr_span.classList.add("number-span");
	nbr_span.appendChild(nbr_txt);
	nbr.appendChild(nbr_span);
	nbr.style.display = 'none'; //Hide this element because the new button is not a stacked request
	
	btn = document.createElement("button");
	btn.type = "button";
	btn.classList.add("btn");
	btn.classList.add("btn-light");
	btn.setAttribute('mark', JSON.stringify(Array(task['mark'])));
	btn.setAttribute('unique_name', task['unique_name']);
	btn.addEventListener('click', function(event){  cancel_task(JSON.parse(this.getAttribute('mark'))[0]); remove_queued_task_button(this); this.blur();});
	btn.tabindex = "-1";
	btn.appendChild(img_holder);
	btn.appendChild(span_type);
	btn.appendChild(span);
	btn.appendChild(nbr);
	
	return btn;
}

function create_button_delegate(task, task_type){
	img = document.createElement("img");
	img.classList.add("button-img");
	img.src = '/fetch_external_media/' +  task['resource_name'];
	
	txt = document.createTextNode(task['display_name']);
	span = document.createElement("span");
	span.classList.add("button-text");
	span.appendChild(txt);
	
	btn = document.createElement("button");
	btn.type = "button";
	btn.classList.add("btn");
	btn.classList.add("btn-primary");
	btn.setAttribute('unique_name', task['unique_name']);
	btn.addEventListener('click', function(event){ delegate(task_type, task['unique_name']); this.blur(); });
	btn.tabindex = "-1";
	btn.appendChild(img);
	btn.appendChild(span);
	
	return btn;
}

function search(searchbox){
	input = searchbox.value.replaceAll(/[^\w\s]/gi, '').replaceAll('_', ' ').toLowerCase().split(' ');
	
	submenu = searchbox.parentNode.parentNode;
	button_groups = submenu.children[2].children;
	for (var i = 1; i < button_groups.length; i++) { //we are ignoring the 'not found' message
		
		if (button_groups[i].style.display === 'none'){
			continue
		}
		buttons = button_groups[i].children;
		buttons = [].slice.call(buttons)
		buttons.sort((a, b) => a.children[1].innerHTML.toLowerCase().localeCompare(b.children[1].innerHTML.toLowerCase()))
		
		all_hidden = true;
		idx = 1; //Start ordering at 1. '0' is reserved for items that need to be reordered
		no_match = [];
		
		for (var j = 0; j < buttons.length; j++) {
			btn = buttons[j];
			match = true;
			txt = btn.getAttribute('unique_name').replaceAll('_', '').replaceAll(/[^\w]/gi, '').toLowerCase();
			for (var query in input){
				if (!txt.includes(input[query])){
					match = false;
				}
			}
			if (!match) {
				//Hide the buttons that do not fit the search query
				//btn.style.display = "none";
				btn.classList.remove('btn-primary');
				btn.classList.add("btn-secondary");
				no_match.push(btn);
			}
			else {
				//Reset the buttons that do fit the search query
				//btn.style.removeProperty( 'display' );
				btn.classList.remove('btn-secondary');
				btn.classList.add("btn-primary");
				all_hidden = false;
				
				//Ignore any negative ordered buttons, they are intended to stay up front
				if (btn.style.order >= 0){
					btn.style.order = idx;
					idx += 1;
				}
			}
		}
		
		// Do some reordering now that we now how many matches we had
		for (var j = 0; j < no_match.length; j++){
			btn = no_match[j];
			
			//Ignore any negative ordered buttons, they are intended to stay up front
			if (btn.style.order >= 0){
				btn.style.order = idx;
				idx += 1;
			}
		}
		
		// Show a little text when we did not find anything
		hide_text = submenu.children[2].children[0];
		if (all_hidden){
			hide_text.style.display = "block";
		}else{
			hide_text.style.display = "none";
		}
	}
}

function switch_tab(tab_link){
	nav = tab_link.parentNode.parentNode;
	tabs = nav.children;
	//for (var i = 0; i < button_groups.length; i++) {
	//	tabs[i].classList.remove("active");
	//}
	tab_link.parentNode.classList.add("active");
}

function switch_tab_content(group_id){
	button_group = document.getElementById(group_id);
	
	if (button_group.style.display === 'none'){
		container = button_group.parentNode;
		button_groups = container.children;
		for (var i = 1; i < button_groups.length; i++) { //we are ignoring the 'not found' message
			button_groups[i].style.display = 'none';
		}
		button_group.style.display = 'flex';
		submenu = button_group.parentNode.parentNode;
		searchbox = submenu.children[1].children[1];
		search(searchbox); //perform a search to order all the items
	}
}

function capitalizeFirstLetter(txt) {
    return txt.charAt(0).toUpperCase() + txt.slice(1);
}
