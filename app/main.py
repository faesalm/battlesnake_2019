import bottle
import os
import random
import numpy as np
from api import *
import time
import collections

# health and length threshold to start getting food
min_health = 30
min_length = 10
global data 
@bottle.route('/')
def static():
	return "the server is running"

@bottle.route('/static/<path:path>')
def static(path):
	return bottle.static_file(path, root='static/')

@bottle.post('/start')
def start():
  return StartResponse("#00ff00")

@bottle.post('/move')
def move():
	s_time =time.time()
	global data
	data = bottle.request.json
	length = data['you']['length']
	health = data['you']['health']
	head = (data['you']['body']['data'][0]['x'],data['you']['body']['data'][0]['y'])

	while health > min_health and length > min_length and (False):
		direction = chase_tail(data)
		return MoveResponse(direction)
	
	board = board_output(data)
	ghost_board = ghost_tail(board)
	num_board = two_pass(ghost_board, data)
	print('Board:')
	print(board)
	print('GhostBoard:')
	print(ghost_board)
	
	# before anything, see if you can kill an adjacent snake (or seriously avoid a spot if they can kill us)
	handle_adj_enemies(board)

	foods = find_closest_food(data, num_board, ghost_board)
	foods = [food for food in foods if food['slack'] >= 0 and food['dist'] != -1]
	print(foods)
	# if there is no food reachable
	if len(foods) == 0:
		# try to chase tail
		print ('chasing tail')
		direction = chase_tail(data)
		if direction != -1:
			return MoveResponse(direction)
		print ('cant chase tail')
		# Do escape box logic if cant chase tail
		possible_boxes = snake_info(num_board)
		# if there are two boxes to pick from, move to bigger one
		if (len(possible_boxes) > 1):
			print 'picking larger box' 
			dict = {}
			for b in possible_boxes:
				# get box_size
				dict[b[0]] = box_info(num_board)[b[0]]
			# label of biggest box
			big_box = max(dict, key=dict.get)
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
		path = bfs(ghost_board, head, closest_food)
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

def chase_tail(data):
	board = board_output(data)
	print(board)
	# head tuple
	head = (data['you']['body']['data'][0]['x'],data['you']['body']['data'][0]['y'])
	# tail tuple
	tail = {"x": data['you']['body']['data'][-1]['x'], "y": data['you']['body']['data'][-1]['y']}
	path = bfs(board,head, tail)
	# if tail is not reachable
	if (len(path) == 0):
		return -1
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


# function that takes in board and returns copy of board with potential enemy moves 
def enemy_moves(board):
	global data
	new_board = board.copy()
	snakes = data['snakes']['data']
	# change name to official name 
	enemies = [s for s in snakes if s['name'] != 'me']
	for enemy in enemies:
		head = (enemy['body']['data'][0]['x'],enemy['body']['data'][0]['y'])
		left = get_left(head)
		right = get_right(head)
		up = get_up(head)
		down = get_down(head)
		# check what is around 
		directions = [up,down,left,right] 
		# remove invalid moves
		directions = [d for d in directions if d != -1]
		for d in directions:
			val = board[d[1]][d[0]]
			# if direction is valid and not body part (assuming they are smart enough not to go there)
			if val not in ('X', 'H'):
				# if val is reachable in one move
				# mark board with h = potential head place
				new_board[d[1]][d[0]] = 'h'				
	return new_board
	

def handle_adj_enemies(board):
	global data
	head = (data['you']['body']['data'][0]['x'],data['you']['body']['data'][0]['y'])
	snakes = data['snakes']['data']
	# change name to official name 
	enemies = [s for s in snakes if s['name'] != 'me']
	for enemy in enemies:
		enemy_head = (enemy['body']['data'][0]['x'],enemy['body']['data'][0]['y'])
		left = get_left(enemy_head)
		right = get_right(enemy_head)
		up = get_up(enemy_head)
		down = get_down(enemy_head)
		# check what is around 
		directions = [up,down,left,right] 
		# remove invalid moves
		directions = [d for d in directions if d != -1]
		for d in directions:
			val = board[d[1]][d[0]]
			# if direction is valid and not body part (assuming they are smart enough not to go there)
			if val not in ('X', 'H'):
				# check if food is reachable next move
				val_tup = {'x': d[0], 'y': d[1]}
				dist = len(bfs(board, head, val_tup))
				if  dist == 2:
					# this is a potential enemy move. check if we can move there
					enemy_length = enemy['length']
					my_length = data['you']['length']
					# if they are smaller, go for this spot
					if enemy_length < my_length:
						print ("enemy is close and smaller. Trying to kill it")
						direction = return_move(head, d)
						return MoveResponse(direction)
					else: 
						print ("enemy is bigger. DO NOT GO HERE")
						board[d[1]][d[0]] = 'X'
	# no enemy is nearby, return -1
	return -1 

def board_output(data):
	#declare game_board as global in method so it can be updated
	board_width = data.get('width')
	board_height = data.get('height')
	#create empty game board.
	game_board = np.empty([board_height, board_width], dtype='string')
	game_board[:] = '-'
	snake_data = data.get('snakes')['data']
	#print(snake_data)
	snakes = []
	food_data = data.get('food')['data']
	#declare game_board as global in method so it can be updated
	for food in food_data:
		x = food['x']
		y = food['y']
		game_board[y][x] = 'F'
	for data in snake_data:
		snakes.append(data.get('body')['data'])	  
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
	board_width = data.get('width')
	board_height = data.get('height')
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
	foods = data['food']['data']
	# food dicts
	foods = [{'x':food['x'],'y': food['y'], 'dist' : -1} for food in foods]
	head = (data['you']['body']['data'][0]['x'], data['you']['body']['data'][0]['y'])
	for food in foods:
		# use bfs to find food distances
		dist = len(bfs(ghost_board, head, food))-1
		food['dist'] = dist
	# sort by distance
	snake_size = len(data['you']['body']['data'])
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
	escape_loc = -1
	body = data['you']['body']['data']
	# check distance from head to every body part
	head = (body[0]['x'],body[0]['y'])
	new_board = game_board.copy()
	# if body is smaller than box size change boxsize to body 
	if len(body) < box_size:
		print 'matching snake and box size' 
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
	print(new_board)
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
			print('removing beause equals x')
			print(coord)
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
			print('adding to valid: ')
			print(coord)
			valid.append(coord)
	# check for an escape route
	if len(escape_routes) != 0:
		# sort paths by length
		escape_routes.sort(key=lambda tup: tup[0])
		# returns direction of first step in longest valid path
		return return_move(head, escape_routes[-1][1])
	else:
		print('no way out')
		if len(valid) == 0:
			print('no valid spot')
			return 'down'
		else:
			print("valid: ")
			print(valid)
			return return_move(head, valid[0])

# returns  list of which boxes the snake belongs to (may be more than 1 for filtering later)
def snake_info(num_board):
	global data
	head = [data['you']['body']['data'][0]['x'], data['you']['body']['data'][0]['y']]
	# get surrounding
	left = get_left(head)
	right = get_right(head)
	up = get_up(head)
	down = get_down(head)
	# check what is around 
	directions = [up,down,left,right]
	l = []
	marked = ['X','T']
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
	body = data['you']['body']['data']
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
		length = data['you']['length']-1
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
	board_width = data.get('width')
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
	board_height = data.get('height') 
	if point[1] == board_height-1: return -1
	return [point[0],point[1]+1]

if __name__ == '__main__':
	bottle.run(
		application,
		host=os.getenv('IP', '0.0.0.0'),
		port=os.getenv('PORT', '8080'),
		debug=True)
