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
	directions = ['up', 'down', 'left', 'right']
	direction = 'right'
	print direction
	return MoveResponse(direction)


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
