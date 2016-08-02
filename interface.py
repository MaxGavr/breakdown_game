from globs import *

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# Functions related to game interface
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

#description of most functions can be found in 'python+libtcod roguelike' article

def render_all(game):
	"render map, GUI and all in-game objects"
	game.camera_pos = move_camera(game.camera_pos, game.player.pos.x, game.player.pos.y)
	game.player.compute_fov()

	#draw environment, including stairs
	for obj in game.location.environment: obj.draw(game.camera_pos, game.consols['map'])
	#draw all items on the level first
	for item in game.location.items: item.draw(game.camera_pos, game.consols['map'])
	#draw all characters on the level
	for character in game.location.characters: character.draw(game.camera_pos, game.consols['map'])
	game.player.draw(game.camera_pos, game.consols['map'])
	
	render_tiles(game)

	#blit the contents of "map_console" to the root console
	libtcod.console_blit(game.consols['map'], 0, 0, CAMERA_WIDTH, CAMERA_HEIGHT, 0, 0, 0)

	#prepare to render GUI panel
	libtcod.console_set_default_background(game.consols['panel'], libtcod.darkest_grey)
	libtcod.console_clear(game.consols['panel'])

	#print the game messages
	game.log.display_messages(game.consols['panel'])

	#show the player's stats
	render_bar(game.consols['panel'], 1, 1, BAR_WIDTH, 'HP', game.player.fighter.hp, game.player.fighter.max_hp, libtcod.red, libtcod.darker_red)

	#show station level
	libtcod.console_print_ex(game.consols['panel'], 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Station level: ' + str(game.location.level))

	#display names of objects under the cursor
	libtcod.console_set_default_foreground(game.consols['panel'], libtcod.light_gray)
	libtcod.console_print_ex(game.consols['panel'], 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_cursor(game))

	#blit the contents of "panel" to the root console
	libtcod.console_blit(game.consols['panel'], 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

def render_tiles(game):
	"go through all tiles, and set their background color"
	local_map = game.location.level_map.map_grid
	for y in range(CAMERA_HEIGHT):
		for x in range(CAMERA_WIDTH):
			(map_x, map_y) = (game.camera_pos[0] + x, game.camera_pos[1] + y)
			color = local_map[map_x][map_y].calculate_color()
			libtcod.console_set_char_background(game.consols['map'], x, y, color, libtcod.BKGND_SET)

def clear_all(game):
	"erase all object icons from their position"
	game.player.clear(game.camera_pos, game.consols['map'])
	for char in game.location.characters:
		char.clear(game.camera_pos, game.consols['map'])
	for item in game.location.items:
		item.clear(game.camera_pos, game.consols['map'])
	for obj in game.location.environment:
		obj.clear(game.camera_pos, game.consols['map'])

def move_camera(camera_pos, target_x, target_y):
	"move the camera, so the (target_x, target_y) is the center"
	#new camera coordinates (top-left corner of the screen relative to the map)
	x = target_x - CAMERA_WIDTH / 2  #coordinates so that the target is at the center of the screen
	y = target_y - CAMERA_HEIGHT / 2
 
	#make sure the camera doesn't see outside the map
	if x < 0: x = 0
	if y < 0: y = 0
	if x > MAP_WIDTH - CAMERA_WIDTH: x = MAP_WIDTH - CAMERA_WIDTH
	if y > MAP_HEIGHT - CAMERA_HEIGHT: y = MAP_HEIGHT - CAMERA_HEIGHT

	return (x, y)

def to_camera_coordinates(camera_pos, x, y):
	"convert coordinates on the map to coordinates on the screen"
	(x, y) = (x - camera_pos[0], y - camera_pos[1])
 
	if x < 0 or y < 0 or x >= CAMERA_WIDTH or y >= CAMERA_HEIGHT:
		return (None, None)  #if it's outside the view, return nothing
 
	return (x, y)

def to_map_coordinates(camera_pos, x, y):
	"convert camera coordinates to position on the map"
	if x < 0 or y < 0 or x >= SCREEN_WIDTH or y >= SCREEN_HEIGHT:
		return (None, None)

	(x, y) = (x + camera_pos[0], y + camera_pos[1])

	return (x, y)

def render_bar(panel, x, y, total_bar_width, name, value, max_value, bar_color, back_color):
	"render GUI bar with specific properties"
	#calculate actual bar width
	bar_width = int(float(value) / max_value * total_bar_width)

	#render the background first
	libtcod.console_set_default_background(panel, back_color)
	libtcod.console_rect(panel, x, y, total_bar_width, 1, False, libtcod.BKGND_SCREEN)

	#render the bar on top
	libtcod.console_set_default_background(panel, bar_color)
	if bar_width > 0:
		libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

	#show the player's stats
	libtcod.console_set_default_foreground(panel, libtcod.white)
	libtcod.console_print_ex(panel, x + total_bar_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(max_value))

def get_names_under_cursor(game):
	"returns the string of names of objects, that are under current position of cursor"
	(x, y) = (mouse.cx, mouse.cy)

	#create a list with the names of all objects at the mouse's coordinates and in FOV
	names = [char.name for char in game.location.characters
				if char.is_here( x, y)
				and char.pos.is_in_fov]
	names += [item.name for item in game.location.items
				if item.is_here(x, y)
				and item.pos.is_in_fov]
	names += [obj.name for obj in game.location.environment
				if obj.is_here(x, y)
				and obj.pos.is_in_fov]

	#join the names, separated by commas
	names = ', '.join(names)
	return names.capitalize()

def menu(header, options, width):
	"display menu window with certain header, list of options to choose from, and width"
	if len(options) > 26:
		raise ValueError('Cannot have a menu with more than 26 options!')

	#calculate total height for the header (after auto-wrap)
	if header == '':
		header_height = 0
	else:
		header_height = libtcod.console_get_height_rect(0, 0, 0, width, SCREEN_HEIGHT, header)

	#total height of the menu window
	height = header_height + len(options)

	#create an off-screen console that represents the menu window
	menu_window = libtcod.console_new(width, height)

	#print the header with auto-wrap
	libtcod.console_set_default_foreground(menu_window, libtcod.white)
	libtcod.console_print_rect_ex(menu_window, width / 2, 0, width, header_height, libtcod.BKGND_NONE, libtcod.CENTER, header)

	#list of letter indexes to draw next to each option
	letter_indexes = [ord('a')]
	for i in range(1, len(options)):
		letter_indexes.append(letter_indexes[-1] + 1)

	#absolute coordinates of the top-left corner of menu_window
	x_absolute = SCREEN_WIDTH / 2 - width / 2
	y_absolute = SCREEN_HEIGHT / 2 - height / 2

	#compute x and y offsets to convert console cursor position to menu position
	x_offset = x_absolute
	y_offset = y_absolute + header_height

	while(True):	
		#print all the options
		for y in range(0, len(options)):
			text = chr(letter_indexes[y]) + ')' + options[y]
			libtcod.console_print_ex(menu_window, 0, y + header_height, libtcod.BKGND_SET, libtcod.LEFT, text)

		#coordinates of cursor inside the menu window
		#menu_y is also the index of the option under cursor
		(menu_x, menu_y) = (mouse.cx - x_offset, mouse.cy - y_offset)
		
		#reprint highlighted option with different background
		if 0 <= menu_x < width and 0 <= menu_y < height - header_height:
			libtcod.console_set_default_background(menu_window, libtcod.grey)
			text = chr(letter_indexes[menu_y]) + ')' + options[menu_y]
			libtcod.console_print_ex(menu_window, 0, menu_y + header_height, libtcod.BKGND_SET, libtcod.LEFT, text)

		#blit the contents of "menu_window" to the root console and present it to the player
		libtcod.console_blit(menu_window, 0, 0, width, height, 0, x_absolute, y_absolute, 1.0, 0.7)
		libtcod.console_flush()
		
		libtcod.console_set_default_background(menu_window, libtcod.black)
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

		if mouse.lbutton_pressed:
			#check if click is within the menu and on a choice
			if 0 <= menu_x < width and 0 <= menu_y < height - header_height:
				return menu_y

		#cancel if the player right-clicked or pressed Escape
		if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
			return None

		#Alt+Enter: toggle fullscreen
		if key.vk == libtcod.KEY_ENTER and key.lctrl:  
			libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
			
		index = key.c - ord('a')
		if 0 <= index < len(options):
			return index

def msgbox(text, width=50):
	"can be used for warning message"
	menu(text, [], width)

def inventory_menu(player, header):
	"show a menu with each item of the inventory as an option"
	if len(player.inventory) == 0:
		options = ['inventory is empty...']
	else:
		options = [item.name for item in player.inventory]

	index = menu(header, options, INVENTORY_WIDTH)

	if index is None or len(player.inventory) == 0:
		return None

	return player.inventory[index]

def equip_menu(player, log):
	"show a menu with items in player's inventory that can be equipped"
	wearable_items = [item for item in player.inventory if item.equip_unit is not None]
	options = [item.name for item in wearable_items]
	if len(options) == 0: options.append('inventory is empty...')

	index = menu('Choose an item to equip', options, INVENTORY_WIDTH)

	if index is not None:
		wearable_items[index].equip_unit.equip()
		log.message('You have equipped ' + options[index] + '.', libtcod.pink)
		player.state = 'acted'

def handle_keys(game):
	"""
		process pressed keys
		main input-handling function
	"""
	player = game.player

	#fullscreen mode with Left Ctrl + Enter
	if key.vk == libtcod.KEY_ENTER and key.lctrl:
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
		
	#exit game with ESC
	elif key.vk == libtcod.KEY_ESCAPE:
		return "exit"

	#key may be redefined, because current control scheme is awful
	#Numpad keys shouldn't be used along with the mouse
	directions = {'1': (-1, 1),  '2': (0, 1),  '3': (1, 1),
				  '4': (-1, 0),                '6': (1, 0),
				  '7': (-1, -1), '8': (0, -1), '9': (1, -1)}

	if game.game_state == 'playing':
		key_char = chr(key.c)

		#handle movements and attack
		if key_char in directions:
			dx = directions[key_char][0]
			dy = directions[key_char][1]
			player.move_or_attack(game, dx, dy)

		elif key_char == '5':
			#wait for one turn
			player.state = 'acted'
			dice = libtcod.random_get_int(0, 0, 4)
			if dice == 0:
				game.log.message('You take a moment to look around...', libtcod.grey)

		elif key_char == 'p':
			#picking up the item
			for item in game.location.items:
				if player.is_here(item.pos.x, item.pos.y):
					item.pick_up(game.log, player, game.location.items)
					break

		elif key_char == 'i':
			#open the inventory
			chosen_item = inventory_menu(player, 'Press the key next to an item to use it, or any other to cancel.\n')
			if chosen_item is not None:
				if chosen_item.equip_unit is None:
					chosen_item.use(game)
				else:
					game.log.message("You should first equip this item.", libtcod.grey)
					player.state = 'idle'
			else:
				player.state = 'idle'

		elif key_char == 'd':
			#open the drop menu
			chosen_item = inventory_menu(player, 'Press the key next to an item to drop it, or any other to cancel.\n')
			if chosen_item is not None:
				chosen_item.drop(game.log, game.location.items)
			else:
				player.state = 'idle'

		elif key_char == '<':
			#go down stairs
			stairs = game.location.environment[0]
			if player.is_here(stairs.pos.x, stairs.pos.y):
				stairs.interact(game)

		elif key_char == 'f':
			#shoot a target with your weapon
			if player.equipment['weapon'] is not None:
				player.equipment['weapon'].owner.use(game)
			else:
				game.log.message("You should first any weapon!", libtcod.grey)
				player.state = 'idle'	

		elif key_char == 'e':
			#open equip menu
			equip_menu(player, game.log)

		elif key_char == 's':
			#just for test; shows whole map
			for tile_row in player.entire_map:
				for tile in tile_row:
					tile.explored = True

		else: player.state = 'idle' #if pressed no key or keys that aren't available

def target_tile(game, max_range = None):
	"""
		return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked
		highlights the line of sight
	"""
	player = game.player

	def highlight_callback(x, y):
		player.entire_map[x][y].highlight()
		return True

	def unhighlight_callback(x, y):
		player.entire_map[x][y].unhighlight()
		return True
	
	while True:
		(x, y) = (mouse.cx, mouse.cy)
		(map_x, map_y) = to_map_coordinates(game.camera_pos, x, y)

		#show the line of sight
		libtcod.line_init(game.player.pos.x, game.player.pos.y, map_x, map_y)
		libtcod.line(game.player.pos.x, game.player.pos.y, map_x, map_y, highlight_callback)

		#redraw map
		render_all(game)
		libtcod.console_flush()
		clear_all(game)

		#hide previous line of sight
		libtcod.line(game.player.pos.x, game.player.pos.y, map_x, map_y, unhighlight_callback)

		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
		(x, y) = (mouse.cx, mouse.cy)
		(map_x, map_y) = to_map_coordinates(game.camera_pos, x, y)

		#if clicked tile is in player's FOV and within max range, return tile's coordinates
		if mouse.lbutton_pressed:
			if not game.player.entire_map[map_x][map_y].is_in_fov:
				game.log.message("You can't see that place.", libtcod.grey)
			elif max_range is not None and player.distance(map_x, map_y) > max_range :
				game.log.message("That place is to far away.", libtcod.grey)
			else:
				return (map_x, map_y)

		#cancel if the player right-clicked or pressed Escape
		if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
			game.log.message("Targeting cancelled...", libtcod.light_grey)
			return (None, None)

def target_enemy(game, max_range = None):
	"returns a clicked enemy inside FOV up to a range, or None if right-clicked"
	while True:
		(x, y) = target_tile(game, max_range)
		if x is None:
			return None

		for char in game.location.characters:
			if char.is_here(x, y):
				return char
		game.log.message("There's no enemy.", libtcod.grey)

def is_targetable(viewer, target):
	"check, whether 'target' object can be targeted from the position of 'viewer' object"

	def target_line_callback(x, y):
		"callback function for 'is_targetable' function"
		if viewer.entire_map[x][y].is_blocked():
			if viewer.is_here(x, y) or target.is_here(x, y):
				return True
			else:
				return False
		else:
			return True
					
	libtcod.line_init(viewer.pos.x, viewer.pos.y, target.pos.x, target.pos.y)

	if not libtcod.line(viewer.pos.x, viewer.pos.y, target.pos.x, target.pos.y, target_line_callback):
		return False
	else:
		return True
