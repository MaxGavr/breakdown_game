from genericobject import Object
from random import choice
from globs import *

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# Environment
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

class Environment(Object):
	"""
		class derived from Object, that represents any background objects: stairs, doors, etc.
		each Environment object can interact with player once it press the right button
		for now only stairs exist
	"""
	def __init__(self, tile, char, color, name, blocks_path = False, always_visible = True, interaction = None):
		"create new background object"
		Object.__init__(self, tile, char, color, name, blocks_path, always_visible)
		self.interaction = interaction #function that is called when character interacts with this object
		
	def interact(self, game):
		"interacting with character"
		if self.interaction is not None:
			self.interaction(game)

def generate_object(station_level): #for now it only constructs down stairs
	"construct new Environment object"
	local_map = station_level.level_map
	(last_x, last_y) = local_map.rooms[-1].center()
	
	obj = Environment(local_map.map_grid[last_x][last_y], '<', libtcod.white, 'stairs', interaction = next_level)
	station_level.environment.append(obj)

def next_level(game):
	"advance to the next game level, 'interact' function for stairs"
	#heal the player by 50%
	game.log.message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
	game.player.fighter.heal(game.player.fighter.max_hp / 2)

	game.log.message('After a rare moment of peace, you ascend the stairs shaft, hoping to get out of this cursed place...', libtcod.lighter_green)

	#reconstruct level
	game.location.__init__(game.location.level - 1)
	
	#place player in one of the rooms
	local_map = game.location.level_map
	starting_room = choice(local_map.rooms)
	game.player.pos = local_map.map_grid[starting_room.center()[0]][starting_room.center()[1]]

	libtcod.console_clear(game.consols['map'])
	for char in game.location.characters:
		char.init_fov()
	game.player.entire_map = local_map.map_grid
	game.player.init_fov()
	game.player.state = 'acted'
