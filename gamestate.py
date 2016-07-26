from random import choice
from globs import *
from gamelog import GameLog
from gamemap import StationLevel
from item import add_item_to_char
from character import generate_player

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# GameState
# Also contains functions, related to global in-game changes
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

class GameState:
	"""
		overall class, contains most needed data
		was implemented in order to get rid of numerous global variables
		it is intended to be universal argument for almost every function
		the best (not really) solution I've figured out so far
	"""
	def __init__(self, current_level, player, log, consols):
		self.location = current_level #GameMap instance, game level as it is
		self.player = player #Player instance, represents the one and only player
		self.log = log #GameLog instance, message log of the current game session

		#game state used for tracking player's death, pause and so on
		#currently used states: 'playing', 'exit'
		self.game_state = 'playing'
		self.consols = consols #libtcod consols dict; consols are used in most UI-functions

def init_new_game():
	"start off a new game session; constructs new GameState instance"
	current_level = StationLevel(10) #starting with level 10
	local_map = current_level.level_map

	#player creation and placing
	starting_room = choice(local_map.rooms)
	(player_x, player_y) = starting_room.center()
	player = generate_player(current_level, player_x, player_y)

	#let our player embark on an adventure with some helpfull items
	#test'em all!!!
	add_item_to_char(player, 0)
	add_item_to_char(player, 1)
	add_item_to_char(player, 2)
	add_item_to_char(player, 3)
	
	#off-screen console
	map_console = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
	#off-screen console for stats panel
	panel_console = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
	consols = {'map': map_console, 'panel': panel_console}
	
	log = GameLog()
	
	current_game = GameState(current_level, player, log, consols)
	return current_game


