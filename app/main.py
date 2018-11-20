import bottle
import os
import random
import numpy as np

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
    board_width = data.get('width')
    board_height = data.get('height')
    #create empty game board.
    game_board = np.chararray((board_height, board_width))
    game_board[:] = '-'
    print game_board

@bottle.post('/move')
def move():
    data = bottle.request.json
    # TODO: Do things with data
    directions = ['up', 'down', 'left', 'right']
    direction = 'right'
    #print direction
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
