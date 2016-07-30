import shelve
from gamestate import init_new_game
from interface import *

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# Main file
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

##########################################################
# System functions
##########################################################

def new_game():
	"start new game, overwriting previous map, player stats, characters, etc."
	current_game = init_new_game()	
	#welcoming message
	current_game.log.message('You hear piercing sound of station alarm. Cold metallic voice of central AI repeats: "Stay in place".', libtcod.lighter_green)
	current_game.log.message('You decide to get out of here, the faster the better.', libtcod.grey)

	return current_game

def play_game(game):
	"start main game loop"

	##########################################################
	# Main loop
	##########################################################

	while not libtcod.console_is_window_closed():

		#catch keyboard/mouse events
		event = libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
		
		#render the screen
		render_all(game)
		libtcod.console_flush()
		
		#erase all objects at their old locations, before they move
		clear_all(game)
			
		#handle keys only if some keyboard/mouse event happened
		if event != 0:
			result = handle_keys(game)
			if result == 'exit':
				return game
		else: #if no keys pressed and mouse clicks, player remains 'idle'
			game.player.state = 'idle'

		#if game is not interrupted and the player made his move, NPCs take their turn
		if game.game_state == 'playing' and game.player.state != 'idle':
			for char in game.location.characters:
				char.ai.take_turn(game, game.player)
 
def main_menu():
	"show main game menu with 3 options: start new game, continue previous game, quit"
	#load background picture
	back_img = libtcod.image_load('back.png')
	
	played_game = None
	while not libtcod.console_is_window_closed():
		#show the background image, at twice the regular console resolution
		libtcod.image_blit_2x(back_img, 0, 0, 0)
		libtcod.console_set_default_foreground(0, libtcod.white)
		libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
            'BREAKDOWN')

		#show options and wait for the player's choice
		choice = menu('', ['Start', 'Continue', 'Quit'], 24)

		if choice == 0:
			game = new_game()
			played_game = play_game(game)
		elif choice == 1:
			try:
				last_game = load_game()
			except:
				msgbox('\n No saved game to load. \n', 24)
				continue
			played_game = play_game(last_game)
		elif choice == 2:
			if played_game is not None:
				save_game(played_game)
			else:
				print "No game to save."
			print "Exiting the game..."
			break

def save_game(game):
	"save game data to the file using 'shelve'"
	print "Saving current game..."
	level = game.location
	
	#save positions of all objects as the list of tuples (x, y)
	char_positions = [(char.pos.x, char.pos.y) for char in level.characters]
	item_positions = [(item.pos.x, item.pos.y) for item in level.items]
	env_positions = [(obj.pos.x, obj.pos.y) for obj in level.environment]
	player_position = (game.player.pos.x, game.player.pos.y)
	#pack it into single list 'positions'
	positions = [char_positions, item_positions, env_positions, player_position]

	#set all tiles and map references to None, so multiple instances of this objects will not be saved during this function
	for char in level.characters:
		char.pos = None
		char.entire_map = None
		char.fov = None
	for item in level.items:
		item.pos = None
	for obj in level.environment:
		obj.pos = None
	game.player.entire_map = None
	game.player.pos = None
	game.player.fov = None

	#also delete references to consols
	game.consols = {}

	#save necessary information to the 'savegame' file
	save_file = shelve.open('savegame', 'n')
	save_file['game'] = game
	save_file['positions'] = positions
	save_file.close()
	print "Current game was sucessfully saved..."

def load_game():
	"load game data from the file using 'shelve'"
	print "Loading last game..."

	#load saved data structures
	load_file = shelve.open('savegame', 'r')
	game = load_file['game']
	positions = load_file['positions']
	load_file.close()

	level = game.location
	
	#recover references to each object's tile and map
	local_map = level.level_map.map_grid
	(char_pos, item_pos, env_pos, player_pos) = positions
	
	game.player.entire_map = local_map
	game.player.pos = local_map[player_pos[0]][player_pos[1]]
	for char in level.characters:
		char.entire_map = local_map
		position = char_pos[level.characters.index(char)]
		char.pos = local_map[position[0]][position[1]]
	for item in level.items:
		position = item_pos[level.items.index(item)]
		item.pos = local_map[position[0]][position[1]]
	for obj in level.environment:
		position = env_pos[level.environment.index(obj)]
		obj.pos = local_map[position[0]][position[1]]

	#recompute FOV for each character
	for char in level.characters:
		char.init_fov()
	game.player.init_fov()

	#initialize new consols
	map_console = libtcod.console_new(CAMERA_WIDTH, CAMERA_HEIGHT)
	panel_console = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
	game.consols = {'map': map_console, 'panel': panel_console}

	print "Previous game was sucessfully loaded..."
	return game

libtcod.console_set_custom_font('dejavu12x12_gs_tc.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Breakdown', False)
libtcod.sys_set_fps(LIMIT_FPS) #set FPS limit

main_menu()
