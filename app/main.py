import bottle
import os
import random
import numpy as np
from api import *
import time
import collections

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
	data = bottle.request.json
	board = board_output(data)
	print(board)
	closest_food = find_closest_food(data)[0]
	# head tuple
	head = (data['you']['body']['data'][0]['x'],data['you']['body']['data'][0]['y'])
	path = bfs(board,head, closest_food)
	direction = return_move(head, path[1])
	f_time = time.time() - s_time
	# if code is too slow
	if f_time >= 0.2:
		print("Execution Time: {}ms".format(round(f_time,3)*1000))
	return MoveResponse(direction)

# run bfs to find closest food 
# return list of tuples (x,y) to food:  [(14, 6), (14, 5), (13, 5), (12, 5)]
def bfs(grid, start,goal, debug = False):
	height, width = len(grid),len(grid[0])
	path = []
	board = grid 
	if debug:
		print goal
	board[goal['y'],goal['x']] = '*'
	g = '*'
	snake = ['H','X','T']
	clear = '-'
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
			return path
		for x2, y2 in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
			if 0 <= x2 < width and 0 <= y2 < height and grid[y2][x2] not in snake and (x2, y2) not in seen:
				queue.append(path + [(x2, y2)])
				seen.add((x2, y2))
	return path

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
	

#Returns list of valid directions to travel (check wall and check self)
def check_move(data):
	me = data.get('you')
	headx = me['body']['data'][0]['x']
	heady = me['body']['data'][0]['y']
	head = (headx, heady)

	trunk_length = len(me['body']['data'])
	my_trunk = []
	if trunk_length>2:
		my_trunk.extend(me.get('body')['data'][1:])

	snek = {'head': {'x': headx, 'y': heady},'trunk': my_trunk}
	directions = ['up', 'down', 'left', 'right']
	directions = check_walls(directions, snek, data)

	directions = check_self(directions, snek, my_trunk)
	return directions

#returns list of valid directions
def check_self(directions, snek, my_trunk):
	for segment in my_trunk:
		trunkx = segment['x']
		trunky = segment['y']
	   
		#check right
		if snek['head']['x']+1 == trunkx and trunky == snek['head']['y']:
			if 'right' in directions:
				directions.remove('right')
		#check left
		if snek['head']['x']-1 == trunkx and trunky == snek['head']['y']:
			if 'left' in directions:
				directions.remove('left')
		#check down
		if snek['head']['y']+1 == trunky and trunkx == snek['head']['x']:
			if 'down' in directions: 
				directions.remove('down')
		#check up
		if snek['head']['y']-1 == trunky and trunkx == snek['head']['x']:
			if 'up' in directions:
				directions.remove('up')
	return directions

def check_walls(directions, snek, data):
	if snek['head']['x'] == 0:
		if 'left' in directions:
			directions.remove('left')
	if snek['head']['y'] == 0:
	   if 'up' in directions:
			directions.remove('up')
	if snek['head']['x'] == data.get('width')-1:
		if 'right' in directions:
			directions.remove('right')
	if snek['head']['y'] == data.get('height')-1:
		if 'down' in directions:
			directions.remove('down')
	return directions
 
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
	

@bottle.post('/end')
def end():
	data = bottle.request.json
	# TODO: Any cleanup that needs to be done for this game based on the data
	#print json.dumps(data)

@bottle.post('/ping')
def ping():
  return "Alive"
	
# return list of dicts of closest foods in order
# format: [{'y': 7, 'x': 11, 'dist': 9}, {'y': 1, 'x': 5, 'dist': 13}]
def find_closest_food(data):
	foods = data['food']['data']
	# food dicts
	foods = [{'x':food['x'],'y': food['y'], 'dist' : -1} for food in foods]
	my_head = {'x':data['you']['body']['data'][0]['x'],'y':data['you']['body']['data'][0]['y']}
	
	for food in foods:
		x_dist = abs(food['x'] - my_head['x'])
		y_dist = abs(food['y'] - my_head['y'])
		total = x_dist + y_dist 
		food['dist'] = total
	# sort by distance
	sorted_foods = sorted(foods, key=lambda k: k['dist'])
	return sorted_foods

# return direction that wont kill us and moves towards closest food	
def go_to_food(data, closest_food, directions):
	
	# maybe if len[directions] == 1	 then we can skip go_to_food
	
	# we will probably have this somewhere else to avoid redundancy
	head_x = data['you']['body']['data'][0]['x']
	head_y = data['you']['body']['data'][0]['y']
	
	# closest_food will be sorted_foods[0]
	food_x, food_y = closest_food['x'], closest_food['y']
	# initialized to a valid direction if all else fails
	direction = directions[0]
	
	# food to left of head
	if head_x > food_x:
		if head_y == food_y and 'left' in directions: direction = 'left'
		elif head_y < food_y and 'down' in directions: direction = 'down'
		elif head_y > food_y and 'up' in directions: direction = 'up'
		else: direction = direction
	# food to right of head:
	elif head_x < food_x:
		if head_y == food_y and 'right' in directions: direction = 'right'
		elif head_y < food_y and 'down' in directions: direction = 'down'
		elif head_y > food_y and 'up' in directions: direction = 'up'
		else: direction = direction
	# else head_x == food_x, food same column
	else:
		if head_y < food_y and 'down' in directions: direction = 'down'
		elif head_y > food_y and 'up' in directions: direction = 'up'
		elif 'right' in directions: direction = 'right'
		else: direction = direction
	print direction
	return direction


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
	bottle.run(
		application,
		host=os.getenv('IP', '0.0.0.0'),
		port=os.getenv('PORT', '8080'),
		debug=True)
