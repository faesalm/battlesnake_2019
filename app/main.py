import bottle
import os
import random
import numpy as np

global game_board
global board_height, board_width
from api import *

@bottle.route('/')
def static():
    return "the server is running"


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    # TODO: Do things with data
    data = bottle.request.json
    global board_width, board_height
    global game_board
    board_width = data.get('width')
    board_height = data.get('height')
    #create empty game board.
    game_board = np.empty([board_height, board_width], dtype='string')
    game_board[:] = '-'

    # TODO: Do things with data
    print(json.dumps(data))

    return StartResponse("#00ff00")

@bottle.post('/move')
def move():
    data = bottle.request.json
    snake_data = data.get('snakes')['data']
    snakes = []
    food_data = data.get('food')['data']
    foods = []

    #declare game_board as global in method so it can be updated
    global game_board

    for food in food_data:
        x = food['x']
        y = food['y']
        game_board[y][x] = 'F'


    for data in snake_data:
        snakes.append(data.get('body')['data'])
        
    # TODO: Do things with data
    print(json.dumps(data))
    
    i = 1
    for snake in snakes:
        print('Snake '+str(i)+':')
        for segment in snake:
            x = segment.get('x')
            y = segment.get('y')
            print 'X: '+str(x)
            print 'Y: '+str(y)+'\n'
            game_board[y][x] = 'X'
        i = i+1
        
    #print current state of game board
    print(game_board)
    # TODO: Do things with data
    directions = ['up', 'down', 'left', 'right']
    direction = 'right'
    #print direction
    #return next move
    direction = random.choice(directions)

    return MoveResponse(direction)


@bottle.post('/end')
def end():
    data = bottle.request.json

    # TODO: Any cleanup that needs to be done for this game based on the data
    print json.dumps(data)


@bottle.post('/ping')
def ping():
    return "Alive"

# Expose WSGI app (so gunicorn can find it)

def board_output(board_width, board_height):
    return 0

application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=True)
