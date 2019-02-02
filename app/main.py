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
	num_board = two_pass(board, data)
	ghost_board = ghost_tail(board)
	print('Board:')
	print(board)
	print('GhostBoard:')
	print(ghost_board)
	print('After two_pass:')
	print(num_board)
	foods = find_closest_food(data, num_board, ghost_board)
	print(foods);
	# if there is no food reachable
	if (foods == -1):
		possible_boxes = snake_info(num_board)
		# if there are two boxes to pick from, move to bigger one
		if len(possible_boxes > 1):
			dict = {}
			for b in possible_boxes:
				# get box_size
				dict[b[0]] = box_info(num_board)[b[0]]
			# label of biggest box
			big_box = max(dict, key=dict.get)
			for b in possible_boxes:
				if b[0] == big_box:
					coord =b[1]
					direction = return_move(head, coord)
					return MoveResponse(direction)
		# else escape
		else:
			direction = escape(data)
			return MoveResponse(direction)
	else:
		closest_food = foods[0]
		# head tuple
		head = (data['you']['body']['data'][0]['x'], data['you']['body']['data'][0]['y'])
		path = bfs(ghost_board, head, closest_food)
		direction = return_move(head, path[1])
	f_time = time.time() - s_time
	# if code is too slow
	if f_time >= 0.2:
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
	if head_x+1 == path_x:
		d = 'right'
	if head_x-1 == path_x:
		d = 'left'
	if head_y-1 == path_y:
		d = 'up'
	if head_y+1 == path_y:
		d = 'down'
	return d


def chase_tail(data):
	board = board_output(data)
	print(board)
	# head tuple
	head = (data['you']['body']['data'][0]['x'],data['you']['body']['data'][0]['y'])
	# tail tuple
	tail = {"x": data['you']['body']['data'][-1]['x'], "y": data['you']['body']['data'][-1]['y']}
	
	path = bfs(board,head, tail)
	direction = return_move(head, path[1])
	return direction


#takes in a board from two_pass and returns a dict w/ unique box labels and the number of times the label occurs
def box_info(num_board):
	info = {}
	i = 0
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
	foods = []
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
	# sort by max slack
	sorted_foods = sorted(foods, key=lambda k: k['slack'])[::-1]
	# sort by min dist
	sorted_foods = sorted(foods, key=lambda k: k['dist'])
	# get rid of unreachable food
	sorted_foods = [food for food in sorted_foods if food['dist'] > 0]
	if (len(sorted_foods) == 0):
		return -1
	return sorted_foods;	
# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()


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
	marked = []
	for d in directions:
		if d != -1 and num_board[d[1]][d[0]] not in marked:
			marked.append(num_board[d[1]][d[0]])
			l.append(num_board[d[1]][d[0]], d)
		else: 
			print d
			print 'not possible'
	# remove Xs and duplicates 
	while 'X' in l:
		l.remove('X')
	while 'T' in l:
		l.remove('T')
	return l

# returns board with 'G' for every body part that will be gone by time snake gets to it 
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
			new_board[dest['y']][dest['x']] = 'G'
		loc +=1
	return new_board

# Helper functions for getting our surroundings. Return -1 if surrounding is out of bounds
def get_right(point):
	global data 
	board_width = data.get('width')
	board_height = data.get('height') 
	if point[0] == board_width-1:
		return -1
	return [point[0]+1,point[1]] 

def get_left(point):
	global data 
	board_width = data.get('width')
	board_height = data.get('height') 
	if point[0] == 0:
		return -1
	return [point[0]-1,point[1]]

def get_up(point):
	global data 
	board_width = data.get('width')
	board_height = data.get('height') 
	if point[1] == 0:
		return -1
	return [point[0],point[1]-1]

def get_down(point):
	global data 
	board_width = data.get('width')
	board_height = data.get('height') 
	if point[1] == board_height-1:
		return -1
	return [point[0],point[1]+1]

if __name__ == '__main__':
	bottle.run(
		application,
		host=os.getenv('IP', '0.0.0.0'),
		port=os.getenv('PORT', '8080'),
		debug=True)
