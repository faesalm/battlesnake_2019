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
    directions = checkMove(data)
    print 'directions in move', 
    print directions,
    direction = random.choice(directions)
    print direction
	#print direction
    return MoveResponse(direction)
    #return direction
    

#Returns list of valid directions to travel
def checkMove(data):
    #taken from Chelsea's repo from last year
    #perhaps this should go into main so that way we could pass snake info to our diff methods without having to rewrite this dict each time
   
    me = data.get('you')
    headx = me['body']['data'][0]['x']
    heady = me['body']['data'][0]['y']
    head = (headx, heady)

    body_length = len(me['body']['data'])
   # print body_length
    my_body = []
    if body_length>2:
        my_body.extend(me['body']['data'][1:-1])

    #print my_body
    tailx = me['body']['data'][-1]['x']
    taily = me['body']['data'][-1]['y']
    tail = (tailx, taily)

    #

    snek = {'head': {'x': headx, 'y': heady},'body': my_body, 'tail': {'x': tailx, 'y': taily}}
    #print snek
    
    directions = ['up', 'down', 'left', 'right']
    
    directions = checkWalls(directions, snek, data)
    
    neckx = snek['body'][0]['x']
    necky = snek['body'][0]['y']
  
    #right now, just making sure snake will not run into neck, but will need to update to not run into any body segments
	#check right
    if snek['head']['x']+1 == neckx or snek['head']['x']+1 == snek['tail']['x']:
		directions.remove('right')
	#check left
    if snek['head']['x']-1 == neckx or snek['head']['x']-1 == snek['tail']['x']:
		directions.remove('left')

	#check down
    if snek['head']['y']+1 == necky or snek['head']['y']+1 == snek['tail']['y']:
	    directions.remove('down')

	#check up
    if snek['head']['y']-1 == necky or snek['head']['y']-1 == snek['tail']['y']:
        directions.remove('up')
    
	# at  this point directions are only valid directions
    
    #directions = ['right']
    return directions

def checkWalls(directions, snek, data):

    if snek['head']['x'] == 0:
        print 'at x min',
        directions.remove('left')
        print directions
    if snek['head']['y'] == 0:
        print 'at y min',
        directions.remove('up')
        print directions
    if snek['head']['x'] == data.get('width')-1:
        print 'at x max',
        directions.remove('right')
        print directions
    if snek['head']['y'] == data.get('height')-1:
        print 'at y max',
        directions.remove('down')
        print directions
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
