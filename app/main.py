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
	#direction = 'right'
    
    directions = checkMove(data)
	#print direction
    direction = random.choice(directions)
    return {'move': direction}

    #return MoveResponse(direction)

#Returns list of valid directions to travel
def checkMove(data):
    #taken from Chelsea's repo from last year
    #perhaps this bit should go into main so that way we could pass snake info to our diff methods without having to rewrite dict each time
    me = data.get('you')
    headx = me['body']['data'][0]['x']
    heady = me['body']['data'][0]['y']
    head = (headx, heady)

    #know this works
    body_length = len(me['body']['data'])
    print 'LENGTH IS ',
    print body_length
    #everything but head and tail
    
    my_body = []

    if body_length>2:
        my_body.append(data.get('body')['data'][1:body_length-2]
    

    #midx = me['body']['data'][(length-1)/2]['x']
    #midy = me['body']['data'][(length-1)/2]['y']
    #mid = (midx, midy)
    tailx = me['body']['data'][(body_length)-1]['x']
    taily = me['body']['data'][(body_length)-1]['y']
    tail = (tailx, taily)

    snek = {'head': {'x': headx, 'y': heady},'body': my_body, 'tail': {'x': tailx, 'y': taily}
}
    directions = ['up', 'down', 'left', 'right']
    
    
    #check walls
    

	#check around head to make sure snake does not run into itself
	#check right
    #if snek['head']['x']+1 == snek['body']['x'] or snek['head']['x']+1 == snek['tail']['x']:
	#	directions.remove('right')
	#check left
    #if snek['head']['x']-1 == snek['body']['x'] or snek['head']['x']-1 == snek['tail']['x']:
	#	directions.remove('left')

	#check down
    #if snek['head']['y']+1 == snek['body']['y'] or snek['head']['y']+1 == snek['tail']['y']:
	#   directions.remove('down')

	#check up
    #if snek['head']['y']-1 == snek['body']['y'] or snek['head']['y']-1 == snek['tail']['y']:
    #   directions.remove('up')
    
	# at  this point directions are only valid directions
    
    #directions = ['right']
    return directions

def checkWalls(directions, snake):
    if snek['head']['x'] == 0:
        directions.remove('left')
    if snek['head']['y'] == 0:
        directions.remove('up')
    if snek['head']['x'] == data.get('width')-1:
        directions.remove('right')
    if snek['head']['y'] == data.get('height')-1:
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
