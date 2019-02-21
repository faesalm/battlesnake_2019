import bottle
import os
import random
import numpy as np
from api import *
import time
import collections


# health and length threshold to start getting food
min_health = 30
min_length = 15
global data
global escapable 
log = True 
@bottle.route('/')
def static():
	return "the server is running"

@bottle.route('/static/<path:path>')
def static(path):
	return bottle.static_file(path, root='static/')

@bottle.post('/start')
def start():
  return StartResponse("#40838e")

@bottle.post('/move')
def move():
	s_time =time.time()
	global data
	data = bottle.request.json
	name = data['you']['name']
	turn = data['turn']
	if log:
		print("Move for turn: " +str(turn))
	length = len(data['you']['body'])
	health = data['you']['health']
	head = (data['you']['body'][0]['x'],data['you']['body'][0]['y'])
	board = board_output(data)
	ghost_board = ghost_tail(board)
	num_board = two_pass(ghost_board, data)
	if log:
		print('Board:')
		print(board)
		print('GhostBoard:')
		print(ghost_board)
	
	# gather information on enemies
	enemy_data = enemy_info(board)
	if log:
		print("ENEMY ASSESSSMENT")
		for e in enemy_data:
			print(e)

	# if any enemy nearby, assess danger and make move accordingly
	nearby_enemies = [e for e in enemy_data if e['nearby_spots'] != []]
	if len(nearby_enemies) != 0:
		print("THERE IS ENEMY NEARBY")
		direction = check_collisions(enemy_data,num_board)
		if direction != -1:
			print ("going to " + str(direction))
			direction = return_move(head,direction)
			return MoveResponse(direction)

	# before anything, see if you can kill an adjacent snake (or seriously avoid a spot if they can kill us)
	#direction = handle_adj_enemies(board)
	# -1 means we are not a step away from any snake, so this logic is skipped
	"""	if direction != -1:
			# we cab potentially kill a snake 
			if direction in ['up','down','left','right']:
				return MoveResponse(direction)
			# we can potentially die
			else: 
				# modify boards so other functions do not try to go for bad spot
				for d in direction:
					ghost_board[d[1]][d[0]] = 'X'
					board[d[1]][d[0]] = 'X'"""
	while health > min_health and length > min_length:
		if log:
			print('chasing tail due to length')
		direction = chase_tail(data,board)
		if direction != -1:
			return MoveResponse(direction)
		else:
			break
	# TODO: Change to ghost foods with ghost tail works well
	foods = find_closest_food(data, num_board, board)
	foods = [food for food in foods if food['slack'] >= 0 and food['dist'] != -1]
	print(foods)
	# if there is no food reachable
	if len(foods) == 0:
		'''
		# try to chase tail
		print ('chasing tail')
		direction = chase_tail(data)
		if direction != -1:
			return MoveResponse(direction)
		print ('cant chase tail')
		# Do escape box logic if cant chase tail
		'''
		possible_boxes = snake_info(num_board)
		# if there are two boxes to pick from, move to bigger one
		if (len(possible_boxes) > 1):
			if log:
				print 'picking larger box' 
			dict = {}
			for b in possible_boxes:
				# get box_size
				dict[b[0]] = box_info(num_board)[b[0]]
			# label of biggest box
			big_box = max(dict, key=dict.get)
			if log:
				print 'bigger box is '
			print(big_box)
			for b in possible_boxes:
				if b[0] == big_box:
					coord =b[1]
					direction = return_move(head, coord)
					return MoveResponse(direction)
		# else escape
		elif (len(possible_boxes) == 1):
			print 'inside one box'
			box_size = box_info(num_board)[possible_boxes[0][0]]
			direction = escape(box_size, board)
			return MoveResponse(direction)
	# else foods are reachable
	else:
		closest_food = foods[0]
		print('closest food is')
		print(closest_food)
		path = bfs(board, head, closest_food)
		print(path)
		direction = return_move(head, path[1])
	f_time = time.time() - s_time
	# if code is too slow
	print("Execution Time: {}ms".format(round(f_time,3)*1000))
	return MoveResponse(direction)

# run bfs to find closest food 
# return list of tuples (x,y) to food:  [(14, 6), (14, 5), (13, 5), (12, 5)]
def bfs(grid, start, goal, debug = False):
	height, width = len(grid),len(grid[0])
	path = []
	board = grid 
	if debug:
		print goal
	tmp = board[goal['y'],goal['x']]
	board[goal['y'],goal['x']] = '*'
	g = '*'
	snake = ['H','X','T']
	queue = collections.deque([[start]])
	seen = set([start])
	while queue:
		path = queue.popleft()
		x, y = path[-1]
		if grid[y][x] == g:
			if debug:
				for p in path[1:-1]:
					board [p[1]][p[0]] = 'P'
				print(board)
			board[goal['y'],goal['x']] = tmp
			return path
		for x2, y2 in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
			if 0 <= x2 < width and 0 <= y2 < height and grid[y2][x2] not in snake and (x2, y2) not in seen:
				queue.append(path + [(x2, y2)])
				seen.add((x2, y2))
	board[goal['y'],goal['x']] = tmp
	return []

def return_move(head, dest):
	next_step = dest
	head_x = head[0]
	head_y = head[1]
	path_x = next_step[0]
	path_y = next_step[1]
	d = ''
	if head_x+1 == path_x: d = 'right'
	if head_x-1 == path_x: d = 'left'
	if head_y-1 == path_y: d = 'up'
	if head_y+1 == path_y: d = 'down'
	return d

#bfs to vals beside tail, with each path take the path which is greater than length 1 and shortest.		
def chase_tail(data,board):
	# head tuple
	head = (data['you']['body'][0]['x'],data['you']['body'][0]['y'])
	# tail tuple
	tail = (data['you']['body'][-1]['x'], data['you']['body'][-1]['y'])
	directions = []
	directions.append(get_left(tail))
	directions.append(get_right(tail))
	directions.append(get_up(tail))
	directions.append(get_down(tail))
	# remove invalid moves
	directions = [d for d in directions if d != -1]
	paths = []
	for d in directions:
		val = board[d[1]][d[0]]
		if val not in ('X', 'T', 'H'):
			tup = {'x': d[0], 'y': d[1]}
			test_path = bfs(board, head, tup)
			if len(test_path) !=0:
				if len(test_path) != 2 : 
					paths.append(test_path)
	if len(paths) == 0: 
		return -1
	elif len(paths) == 1: 
		path = paths[0]
		direction = return_move(head, path[1])
		return direction
	else: # more than one potential path to tail
		path = paths[0]
		paths = [p for p in paths if len(p) > 2]
		for p in paths:
			if len(path) == 2: 
				path = p
			else:
				if len(p) < len(path): path = p
		direction = return_move(head, path[1])
		return direction


#takes in a board from two_pass and returns a dict w/ unique box labels and the number of times the label occurs
def box_info(num_board):
	info = {}
	board_width = len(num_board)
	board_height = len(num_board[0])
	for x in range(board_width):
		for y in range(board_height):
			key = num_board[x][y]
			if key == 'X' or key == 'T' or key == 'H':
				continue
			if key in info:
				info[key] += 1
			else:
				info[key] = 1
	return info


# function to calculate potential moves of enemies and either attacks that position or marks it with an 'X' as it is dangerous. 
# skipped if no enemies nearby. Returns list of bad positions. -1 if function is irrelavent
# TODO: Fix this to handle multiple enemies and make smarter decisions based on enemy_info()
def handle_adj_enemies(board):
	global data
	name = data['you']['name']
	head = (data['you']['body'][0]['x'],data['you']['body'][0]['y'])
	snakes = data['board']['snakes']
	# change name to official name 
	enemies = [s for s in snakes if s['name'] != name]
	for enemy in enemies:
		enemy_head = (enemy['body'][0]['x'],enemy['body'][0]['y'])
		left = get_left(enemy_head)
		right = get_right(enemy_head)
		up = get_up(enemy_head)
		down = get_down(enemy_head)
		# check what is around 
		directions = [up,down,left,right] 
		# remove invalid moves
		directions = [d for d in directions if d != -1]
		bad_directions = []
		for d in directions:
			val = board[d[1]][d[0]]
			# if direction is valid and not body part (assuming they are smart enough not to go there)
			if val not in ('X', 'H'):
				# check if food is reachable next move
				val_tup = {'x': d[0], 'y': d[1]}
				path = bfs(board, head, val_tup)
				dist = len(path)
				if  dist == 2:
					# this is a potential enemy move. check if we can move there
					enemy_length = len(enemy['body'])
					my_length = len(data['you']['body'])
					# if they are smaller, go for this spot
					if enemy_length < my_length:
						if log:
							print ("enemy is close and smaller. Trying to kill it by going to: " + str(path[1]))
						direction = return_move(head, path[1])
						return direction
					else: 
						if log:
							print ("enemy is bigger. DO NOT GO HERE: " + str(path[1]))
						bad_directions.append(d)
	# either return list of bad directions or return -1 if we are not close to other snakes (making this function useless)
	if len(bad_directions) > 0:
		return bad_directions
	return -1 

# returns (x,y) move
"""
	Engine for handling nearby enemies
	Logic:
	0. if we can go only 1 place, return that.
	1. if any enemy has one spot to go and we can reach that spot:
		- kill enemy if we are larger
		- avoid that spot as they will go there and kill us 
	2. if we have more than 1 choice and enemy has 1+ choice:
		if there are escapable spots and if spot is safe (risky but not guaranteed to die):
			case 1 (aggressive): if any smaller enemy can go here: 
				attack (no risk of getting stuck since it is escapable)
			
			case 2 (conservative): no enemy can go here: 
				take this direction
			
			default case (if other 2 return empty): if any bigger enemy can go here:
				try to avoid, but still go for it if only escapable spot
			
			cases are executed in that order (possibly change mode depending on gameplay)
		
		#TODO: consider if spot is both dangerous and can kill snake 
		#TODO: consider how many moves enemy has
		#TODO: consider how many enemies can attack a spot

		if no escapable boxes: 




"""
def check_collisions(enemy_data, board, mode = 'aggressive'):
	# only consider nearby enemies
	enemies = [e for e in enemy_data if e['nearby_spots'] != []]
	# directions are our valid moves
	head = (data['you']['body'][0]['x'],data['you']['body'][0]['y'])
	directions = []
	valid = []
	directions.append(get_left(head))
	directions.append(get_right(head))
	directions.append(get_up(head))
	directions.append(get_down(head))
	# remove invalid moves
	directions = [d for d in directions if d != -1]
	for d in directions:
		val = board[d[1]][d[0]]
		if val not in ('X', 'T', 'H'):
			valid.append(d)

	# Base cases if one have only no/one possible move to make
	# no valid moves so we are dead next turn. Return 'down' 
	if len(valid) == 0:
		return get_down(head)
	#if we have one move take that move
	if len(valid) == 1:
		return valid[0]

	"""
	if we have 2+ possible moves and enemy has one possible move
		if they are smaller kill them (will always work since they have one possible move)
		# are they bigger?
			# never move to their one move 
			# test other moves with box info
	"""
	if len(valid) > 1:
		# we have 2+ choices and they have 1 choice. Decide if to avoid or intercept their move based on size
		for e in enemies:
			# check if enemy has one possible move and we can reach it
			if len(e['possible_moves']) == 1 and e['possible_moves'][0] in e['nearby_spots']:
				if not e['bigger']:
					if log:
						print('We can 100% kill {}. Going to {}'.format(e['name'], e['possible_moves'][0]))
					return e['possible_moves'][0]
				# they are bigger than us and they WILL move to this spot, so avoid no matter what
				else: 
					bad = e['possible_moves'][0]
					if log:
						print('{} can 100% kill us if we go to {}, so avoid it'.format(e['name'], e['possible_moves'][0]))
					valid.remove(bad)


	# we have 2+ choices and at most 2 that can potentially cause collision
	# spots that are valid and will not kill us 
	safe_spots = valid
	# remove spots that lead to boxes that are not escapable
	box_sizes = []
	for spot in valid:
		spot_num = board[spot[1]][spot[0]]
		box_size = box_info(board)[spot_num]
		tup = [spot,box_size]
		box_sizes.append(tup)
		direction = escape(box_size,board)
		if not escapable:
			safe_spots.remove(spot)
	# sort for biggest 
	# (x,y), box_size pair for every escapable spot. Sorted from largest to smallest box_size 
	box_sizes.sort(key=lambda x: x[1], reverse = True)
	print(box_sizes)

	# target spot 
	goal = -1
	"""
		if there are escapable spots and if spot is safe (risky but not guaranteed to die):
			case 1 (aggressive): if any smaller enemy can go here: 
				attack (no risk of getting stuck since it is escapable)
			
			case 2 (conservative): no enemy can go here: 
				take this direction

			default case (if other 2 return empty): if any bigger enemy can go here:
				try to avoid, but still go for it if only escapable spot
			
			cases are executed in that order (possibly change mode depending on gameplay)

	"""

	# aggressive: try to kill enemies first
	if mode == 'aggressive':
		for spot in box_sizes:
			if spot[0] in safe_spots:
				can_kill = False
				print('Spot {} is possibly safe with size of {} '.format(spot[0],spot[1]))
				# pick an escapable potential kill
				for e in enemies:
					if spot[0] in e['nearby_spots'] and not e['bigger']:
							print('Spot {} can kill {}'.format(spot[0],e['name']))
							can_kill = True
							goal = spot[0]
				# if found a spot that can kill, return since this is biggest box
				if can_kill:
					break
				# TODO: consider if we can kill snake
			else:
				print('Spot {} is NOT safe '.format(spot[0]))
		# if target is found 
		if goal != -1:
			print('going for {}: safe and can kill an enemy'.format(goal))
			return goal 


		found_safe = False
		# if not try to find an escapable and not dangerous spot
		for spot in box_sizes:
			if spot[0] in safe_spots:
				danger = False
				print('Spot {} is possibly safe with size of {} '.format(spot[0],spot[1]))
				# pick an escapable and not dangerous path
				for e in enemies:
					if spot[0] in e['nearby_spots'] and e['bigger']:
							print('Spot {} is dangerous because of {}'.format(spot[0],e['name']))
							danger = True
							goal = spot[0]
				# if found a spot that can kill, return since this is biggest box
				if not danger:
					goal = spot[0]
					found_safe = True
					break
			else:
				print('Spot {} is NOT safe '.format(spot[0]))
		# if safe spot found
		if found_safe:
			print('going for {}: safe and no one can kill us'.format(goal))
			return goal

	# TODO: implement conservative mode (just reorder aggressive)
	if mode == 'conservative':
		pass

	# if all blocks are dangerous and no potential kills, just return best escapable spot and hope for the best 
	if len(box_sizes) != 0:
		return box_sizes[0][0]



	# -1 is just signaling no more cases are actually handled in this function so ignore it
	return -1

	"""	
		# if no escapable spots.
			if safe_spots == []:
				# if they are smaller: go for the bigger box in nearby_spots
				for box in box_sizes:
					if box in e['nearby_spots']:
						return box[0]
			# TODO: decide which is better spot if more than one
			for spot in safe_spots:
				# if enemy is smaller and box is escapable, attack
				if not e['bigger'] and spot in e['nearby_spots']:
					return spot
	return -1

	"""
	#if we have 2+ moves and they do too
		# find biggest box of our possible moves and eliminate bad boxes
			# if they are a smaller snake and the possible collision is in a good box. try it
			# if we can completely avoid collisions( safe moves )
			# take it always if they are bigger 
			# if they are bigger and there are no safe moves go for biggest box
	
# function to gather basic information on all enemies. Decision making is done in other functions
# Returns a list of dicts. Format: {'possible_moves': [[8, 8], [9, 9]], 'nearby_spots': [], 'name': 'enemy', 'bigger': False}
def enemy_info(board):
	global data
	head = (data['you']['body'][0]['x'],data['you']['body'][0]['y'])
	snakes = data['board']['snakes']
	name = data['you']['name']
	# change name to official name 
	enemies = [s for s in snakes if s['name'] != name]
	enemy_info = []
	for enemy in enemies:
		enemy_dict = {}
		enemy_head = (enemy['body'][0]['x'],enemy['body'][0]['y'])
		left = get_left(enemy_head)
		right = get_right(enemy_head)
		up = get_up(enemy_head)
		down = get_down(enemy_head)
		# check what is around 
		directions = [up,down,left,right] 
		# remove invalid moves
		directions = [d for d in directions if d != -1]
		enemy_dict['name'] = enemy['name'].encode("utf-8")
		enemy_dict['possible_moves'] = []
		# bad_directions = []
		enemy_dict['nearby_spots'] = []
		# calculate if enemy is bigger or same size
		if len(enemy['body'])< len(data['you']['body']):
			enemy_dict['bigger'] = False
		else: 
			enemy_dict['bigger'] = True

		for d in directions:
			val = board[d[1]][d[0]]
			# if direction is valid and not body part (assuming they are smart enough not to go there)
			if val not in ('X', 'H', 'T'):
				enemy_dict['possible_moves'].append(d)
				# check if food is reachable next move
				val_tup = {'x': d[0], 'y': d[1]}
				path = bfs(board, head, val_tup)
				dist = len(path)
				if  dist == 2:
					enemy_dict['nearby_spots'].append(d) 
		enemy_info.append(enemy_dict)
	return enemy_info

def board_output(data):
	#declare game_board as global in method so it can be updated
	board_width = data['board']['width']
	board_height = data['board']['height']
	#create empty game board.
	game_board = np.empty([board_height, board_width], dtype='string')
	game_board[:] = '-'
	snake_data = data['board']['snakes']
	#print(snake_data)
	snakes = []
	food_data =  data['board']['food']
	#declare game_board as global in method so it can be updated
	for food in food_data:
		x = food['x']
		y = food['y']
		game_board[y][x] = 'F'
	for data in snake_data:
		snakes.append(data.get('body'))	  
	i = 1
	for snake in snakes:
		j = 0
		for segment in snake:
			x = segment.get('x')
			y = segment.get('y')
			#Set head
			if j == 0:
				game_board[y][x] = 'H'
			#Set tail
			elif j == len(snake)-1:
				game_board[y][x] = 'T'
			else:
				game_board[y][x] = 'X'
			j = j+1
		i = i+1
	#print current state of game board
	return game_board
	#reset board after print output of move.

# takes in board created by board_output and returns a copy divided into numbered boxes
def two_pass(board, data):
	board_width = data['board']['width']
	board_height = data['board']['height']
	num_board = board.copy()
	labels = []
	curr_id = 0
	labels.append(str(curr_id))
	# first pass
	for y in range(board_height):
		for x in range(board_width):
			if num_board[y][x] == '-' or num_board[y][x] == 'F': 
				# check neighbour labels (since we go top left to bot right, right and down never visited before current place)
				neighbours = []
				if y != 0 and num_board[y-1][x].isdigit(): neighbours.append(num_board[y-1][x]) # up
				if x != 0 and num_board[y][x-1].isdigit(): neighbours.append(num_board[y][x-1]) # left
				if len(neighbours) == 0:
					num_board[y][x] = curr_id
					curr_id += 1
					labels.append(str(curr_id))
				elif len(neighbours) == 1 or int(neighbours[0]) == int(neighbours[1]):
					num_board[y][x] = neighbours[0]
				else: # 2 diff neighbours 
					# set label to smallest neighbour label
					smaller = labels[int(min(neighbours))]
					num_board[y][x] = smaller # set curr place to min neighbour
					labels[int(max(neighbours))] = smaller # set label of larger nb to smaller
					# when a relabel occurs change all other boxes to new label(showing they are all connected)
					for box in range(len(labels)): 
						if labels[box] == max(neighbours): labels[box] = smaller
	# last item of labels list always unused so delete it
	del labels[-1]
	# second pass
	for y in range(board_height):
		for x in range(board_width):
			curr = num_board[y][x]
			# if number on the board is not correct label change to new label
			if curr.isdigit() and labels[int(curr)] != curr:
				num_board[y][x] = labels[int(curr)]
	return num_board

@bottle.post('/end')
def end():
	data = bottle.request.json
	# TODO: Any cleanup that needs to be done for this game based on the data
	#print json.dumps(data)

@bottle.post('/ping')
def ping():
  return "Alive"
	
# return list of dicts of closest foods in order
# format: [{'y': 14, 'x': 11, 'dist': 1, 'slack': 102}, {'y': 7, 'x': 3, 'dist': 14, 'slack': 89}]
def find_closest_food(data, num_board, ghost_board):
	foods = data['board']['food']
	# food dicts
	foods = [{'x':food['x'],'y': food['y'], 'dist' : -1} for food in foods]
	head = (data['you']['body'][0]['x'], data['you']['body'][0]['y'])
	for food in foods:
		# use bfs to find food distances
		dist = len(bfs(ghost_board, head, food))-1
		food['dist'] = dist
	# sort by distance
	snake_size = len(data['you']['body'])
	# check which box food is in
	for food in foods:
		# box food is in 
		box = num_board[food['y'],food['x']]
		# size of board
		box_size = box_info(num_board)[box]
		food['slack'] = box_size - snake_size
	sorted_foods = sorted(foods, key= lambda k: (k['dist'], -k['slack']))
	if (len(sorted_foods) == 0):
		return []
	return sorted_foods	
# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

# when no food reachable attempt to create a valid bfs path from head to an escape location
# the escape loc is defined as point that will be clear reachable by bfs
# we take the longest valid bfs path from beside our head that still reaches this escape loc
def escape(box_size, game_board):
	c_list = []
	global escapable
	escape_loc = -1
	body = data['you']['body']
	# check distance from head to every body part
	head = (body[0]['x'],body[0]['y'])
	new_board = game_board.copy()
	# if body is smaller than box size change boxsize to body 
	if len(body) < box_size:
		if log:
			#print 'matching snake and box size' 
			box_size = len(body)
	# mark last box_size (n) of body (in reverse order because closer to tail is better)
	c_list = body[-box_size::]
	c_list = c_list[::-1]
	for c in c_list:
		new_board[c['y']][c['x']] = 'C'
	# get closest C location with a valid bfs path
	curr = 0
	for c in c_list:
		curr += 1
		x_y = {'x':c['x'], 'y':c['y']}
		path = bfs(game_board,head,x_y)
		# found valid path with length >= distance from tail to ensure good escape location
		if path != [] and len(path) >= curr:
			escape_loc = c
			new_board[escape_loc['y']][escape_loc['x']] = '*'
			break
	# print(new_board)
	# bfs to escape_loc from squares adj to head or find valid locations to move
	escape_routes = []
	valid = []
	adj = []
	adj.append(get_left(head))
	adj.append(get_right(head))
	adj.append(get_up(head))
	adj.append(get_down(head))
	# test each bfs path from each coord to escape location
	for coord in adj:
		# if invalid direction (edge of board)
		if coord == -1:
			continue
		# if invalid direction (snake body)
		# might need to check for more than just 'X' spots in the future(maybe T for other snakes)
		if game_board[coord[1]][coord[0]] == 'X':
			#print('removing because equals x')
			#print(coord)
			continue
		# test bfs path if there is an escape location
		if escape_loc != -1:
			tup = (coord[0],coord[1])
			route = bfs(game_board, tup, escape_loc)
			# move along if bfs does not reach escape_loc
			if len(route) == 0:
				continue
			else:
				# append length of valid path and its direction to take for path
				escape_routes.append((len(route), coord))
		else: 
			# valid routes are backup in case of no escape route
			#print('adding to valid: ')
			#print(coord)
			valid.append(coord)
	# check for an escape route
	if len(escape_routes) != 0:
		escapable = True
		# sort paths by length
		escape_routes.sort(key=lambda tup: tup[0])
		# returns direction of first step in longest valid path
		return return_move(head, escape_routes[-1][1])
	else:
		escapable = False
		print('no way out')
		if len(valid) == 0:
			print('no valid spot')
			return 'down'
		else:
			#print("valid: ")
			print(valid)
			return return_move(head, valid[0])

# returns  list of which boxes the snake belongs to (may be more than 1 for filtering later)
def snake_info(num_board):
	global data
	head = [data['you']['body'][0]['x'], data['you']['body'][0]['y']]
	# get surrounding
	left = get_left(head)
	right = get_right(head)
	up = get_up(head)
	down = get_down(head)
	# check what is around 
	directions = [up,down,left,right]
	l = []
	marked = ['X','T', 'H']
	for d in directions:
		if d == -1:
			continue
		num = num_board[d[1]][d[0]]
		if num not in marked:
			marked.append(num_board[d[1]][d[0]])
			l.append((num_board[d[1]][d[0]], d))
	return l

# returns board with 'G' for every body part t hat will be gone by time snake gets to it 
def ghost_tail(board, debug = False):
	global data
	new_board = board.copy()
	body = data['you']['body']
	# check distance from head to every body part
	head = (body[0]['x'],body[0]['y'])
	loc = 2
	for b in body[2:]:
		# get distance to body part
		dest = {'x':b['x'],'y': b['y']}
		path = bfs(new_board, head, dest)[1:]
		dist = len(path)
		if debug:
			print ("distance to:" + str(dest))
			print(path)
			print(dist)
		# check if body part will be gone by comparing how far it is to tail with how far it takes to reach it
		length = len(data['you']['body'])-1
		diff = length - loc
		# body part will be gone if it is closer to tail than distance to it
		# special case for tail (diff == 0). This is likely a rule change for 2019 so maybe delete
		if (diff < dist and diff != 0):
			new_board[dest['y']][dest['x']] = '-'
		loc +=1
	return new_board

# Helper functions for getting our surroundings. Return -1 if surrounding is out of bounds
def get_right(point):
	global data 
	board_width = data['board']['width']
	if point[0] == board_width-1: return -1
	return [point[0]+1,point[1]] 

def get_left(point):
	global data 
	if point[0] == 0: return -1
	return [point[0]-1,point[1]]

def get_up(point):
	global data 
	if point[1] == 0: return -1
	return [point[0],point[1]-1]

def get_down(point):
	global data
	board_height = data['board']['height']
	if point[1] == board_height-1: return -1
	return [point[0],point[1]+1]

if __name__ == '__main__':
	bottle.run(
		application,
		host=os.getenv('IP', '0.0.0.0'),
		port=os.getenv('PORT', '8080'),
		debug=True)
