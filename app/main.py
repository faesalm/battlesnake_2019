import bottle
import os
import random
import numpy as np

global game_board
global board_height, board_width

@bottle.route('/')
def static():
    return "the server is running"


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    # TODO: Do things with data
	#return {'Orange': 0xffa500}
    data = bottle.request.json
    global board_width, board_height
    global game_board
    board_width = data.get('width')
    board_height = data.get('height')
    #create empty game board.
    game_board = np.chararray((board_height, board_width))
    game_board[:] = '-'

@bottle.post('/move')
def move():
    data = bottle.request.json
    snake_data = data.get('snakes')['data']
    snakes = []
    #declare game_board as global in method so it can be updated
    global game_board
    global board_width, board_height
    for data in snake_data:
        snakes.append(data.get('body')['data'])
    
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
        
    # TODO: Do things with data
    directions = ['up', 'down', 'left', 'right']
    direction = 'right'
    #print direction
    print(game_board)
    #return next move
    return {'move': direction}

# Expose WSGI app (so gunicorn can find it)

def board_output(board_width, board_height):
    return 0

application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug = True)
