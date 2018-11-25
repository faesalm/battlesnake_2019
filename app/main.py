import bottle
import os
import random

from api import *

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
    data = bottle.request.json
    directions = check_move(data)
    direction = random.choice(directions)
    return MoveResponse(direction)  

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


@bottle.post('/end')
def end():
	data = bottle.request.json

	# TODO: Any cleanup that needs to be done for this game based on the data
	print json.dumps(data)


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

def board_output():
	return 0

# Expose WSGI app (so gunicorn can find it)

application = bottle.default_app()

if __name__ == '__main__':
	bottle.run(
		application,
		host=os.getenv('IP', '0.0.0.0'),
		port=os.getenv('PORT', '8080'),
		debug=True)
