import random
from character import generate_enemy
from environment import generate_object
from item import add_item_to_lvl
from globs import *

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# StationLevel, GameMap, Tile, Rectangle
# May conatain functions, related to map generation
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

class StationLevel:
	"""
		single level of in-game location
		contains map of the level, also characters, items and other objects (i. e. stairs, doors) located here
	"""
	def __init__(self, level):
		"create new level"
		self.level_map = GameMap()

		#for now, it's just a number, that indicates how far you get in exploring the station
		self.level = level

		#lists of different objects, that reside on this level
		self.environment = []
		self.items = []
		self.characters = []

		self.place_enemies()
		self.place_items()
		self.place_stairs()

	def get_player_start_pos(self):
		"returns coordinates of the center of the starting room, where player will be placed"
		return self.level_map.starting_room.center()

	def place_enemies(self):
		"fill the station level with enemies"
		local_map = self.level_map.map_grid
		for room in self.level_map.rooms:
			if room != self.level_map.starting_room:
				num_enemies = libtcod.random_get_int(0, 0, MAX_ROOM_ENEMIES)
				
				for i in range(num_enemies):
					#choose a random spot for an enemy
					x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
					y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

					#very poor mechanism of calculating chances
					dice = libtcod.random_get_int(0, 0, 100)
					if not local_map[x][y].is_blocked():
						if dice < 80:
							generate_enemy(self, x, y, 0)
						else:
							generate_enemy(self, x, y, 1)

	def place_items(self):
		"fill rooms with items"
		local_map = self.level_map.map_grid
		for room in self.level_map.rooms:
			num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)
			
			for i in range(num_items):
				#choose random spot for an item
				x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
				y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

				if not local_map[x][y].is_blocked():
					#roll the dice to know which item to generate
					dice = libtcod.random_get_int(0, 0, 100)

					if dice < 70:
						add_item_to_lvl(self, x, y, 0)
					elif dice < 70 + 10:
						add_item_to_lvl(self, x, y, 1)
					elif dice < 70 + 10 + 10:
						add_item_to_lvl(self, x, y, 2)
					else:
						add_item_to_lvl(self, x, y, 3)

		#place laser rifle in a random room; for now it's just for testing
		gun_room = random.choice(self.level_map.rooms)
		add_item_to_lvl(self, gun_room.center()[0], gun_room.center()[1], 6)

	def place_stairs(self):
		"create stairs at the center of the last room"
		generate_object(self)

	def closest_enemy(self, viewer, max_range):
		"find closest enemy, up to a maximum range and in the viewer's FOV"
		closest_enemy = None
		closest_dist = max_range + 1

		for char in self.characters:
			if char.pos.is_in_fov:
				#calculate distance between this object and the player
				dist = viewer.distance_to(char)
				if dist < closest_dist:
					closest_enemy = char
					closest_dist = dist

		return closest_enemy

class Tile:
	"""
		a tile of the map with its properties
		it doesn't have any information about the objects placed on the top of itself
	"""
	def __init__(self, x, y, tile_type, occupied = False):
		"create new tile with certain position and type"
		#coordinates of this tile according to the level's map
		self.x = x
		self.y = y

		self.set_type(tile_type)
		
		self.occupied = occupied #indicates, if this tile is occupied by some object
		self.explored = False #shows, if this tile has ever been in the FOV of the player
		self.is_in_fov = False #shows, if this tile is currently in the FOV of the player
		self.highlighted = False #highlighting matters in the 'calculate_color' function

	def set_type(self, tile_type):
		"""
			set general propeties of the tile, based on its type
			types and basic explanations can be seen in TILE_TYPES 
		"""
		its_type = TILE_TYPES[tile_type] #explanation in 'globs.py'
		
		self.title = its_type['title']
		self.walkable = its_type['walkable']
		self.transparent = its_type['transparent']
		self.l_color = its_type['vis_color']
		self.d_color = its_type['hid_color']
		self.hi_color = its_type['hi_color']

	def is_blocked(self):
		"return True if this block can be crossed by a character"
		if not self.walkable:
			return True
		elif self.occupied:
			return True
		else:
			return False

	def highlight(self):
		self.highlighted = True

	def unhighlight(self):
		self.highlighted = False

	def calculate_color(self):
		"determine the color of the tile, based on its properties"
		if not self.explored:
			return libtcod.black
			
		if self.is_in_fov:
			if self.highlighted:
				return self.hi_color
			else:
				return self.l_color
		else:
			return self.d_color

class GameMap:
	"""
		map of the in-game location
		simply speaking, a two-dimensional list of tiles
		also contains rooms and corridors
	"""
	def __init__(self):
		"create map using BSP"
		#fill map with impassable tiles
		self.map_grid = [ [Tile(x, y, 'wall') for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH) ]

		self.rooms = [] #rooms on current map, presented by Rectangle instances
		
		#new root node
		bsp = libtcod.bsp_new_with_size(0, 0, MAP_WIDTH, MAP_HEIGHT)

		#split into nodes
		libtcod.bsp_split_recursive(bsp, 0, DEPTH, ROOM_MIN_SIZE + 1, ROOM_MIN_SIZE + 1, 1.5, 1.5)

		#traverse the nodes and create rooms
		libtcod.bsp_traverse_inverted_level_order(bsp, self.traverse_node)

		self.choose_starting_room()

	def traverse_node(self, node, dat):
		"callback-function for BSP map generating"
		if libtcod.bsp_is_leaf(node): #if node is a leaf, create room
			min_x = node.x + 1
			max_x = node.x + node.w - 1
			min_y = node.y + 1
			max_y = node.y + node.h - 1
			
			if max_x == MAP_WIDTH - 1: max_x -= 1
			if max_y == MAP_HEIGHT - 1: max_y -= 1

			#randomize room size if FULL_ROOMS is disabled
			if FULL_ROOMS == False:
				min_x = libtcod.random_get_int(0, min_x, max_x - ROOM_MIN_SIZE + 1)
				min_y = libtcod.random_get_int(0, min_y, max_y - ROOM_MIN_SIZE + 1)
				max_x = libtcod.random_get_int(0, min_x + ROOM_MIN_SIZE - 2, max_x)
				max_y = libtcod.random_get_int(0, min_y + ROOM_MIN_SIZE - 2, max_y)

			node.x = min_x
			node.y = min_y
			node.w = max_x - min_x + 1
			node.h = max_y - min_y + 1

			new_room = Rectangle(node.x, node.y, node.w - 1, node.h - 1)
			self.create_room(new_room)

		else: #if the node is not a leaf, connect its left and right children
			
			left = libtcod.bsp_left(node)
			right = libtcod.bsp_right(node)
			node.x = min(left.x, right.x)
			node.y = min(left.y, right.y)
			node.w = max(left.x + left.w, right.x + right.w) - node.x
			node.h = max(left.y + left.h, right.y + right.h) - node.y

			if node.horizontal: #if node is splitted horizontally
				#if left and right nodes intersect
				if left.x + left.w - 1 < right.x or right.x + right.w - 1 < left.x:
					x1 = libtcod.random_get_int(0, left.x , left.x + left.w - 1)
					x2 = libtcod.random_get_int(0, right.x , right.x + right.w - 1)
					y = libtcod.random_get_int(0, left.y + left.h, right.y)
					self.create_vert_line_up(x1, y - 1)
					self.create_hor_line(y, x1, x2)
					self.create_vert_line_down(x2, y + 1)

				#if left and right nodes do not intersect
				else:
					min_x = max(left.x + 1, right.x + 1)
					max_x = min(left.x + left.w - 1, right.x + right.w - 1)
					x = libtcod.random_get_int(0, min_x, max_x)
					self.create_vert_line_down(x, right.y)
					self.create_vert_line_up(x, right.y - 1)
			else: #if node is splitted vertically
				#if left and right nodes intersect
				if left.y + left.h - 1 < right.y or right.y + right.h - 1 < left.y:
					y1 = libtcod.random_get_int(0, left.y + 1, left.y + left.h - 1)
					y2 = libtcod.random_get_int(0, right.y + 1, right.y + right.h - 1)
					x = libtcod.random_get_int(0, left.x + left.w + 1, right.x)
					self.create_hor_line_left(x - 1, y1)
					self.create_vert_line(x, y1, y2)
					self.create_hor_line_right(x + 1, y2)

				#if left and right nodes do not intersect
				else:
					min_y = max(left.y + 1, right.y + 1)
					max_y = min(left.y + left.h - 1, right.y + right.h - 1)
					y = libtcod.random_get_int(0, min_y, max_y)
					self.create_hor_line_left(right.x - 1, y)
					self.create_hor_line_right(right.x, y)
		return True
	
	def create_room(self, room):
		"carve rectangle room"
		#go through the tiles in the rectangle and make them passable by changing their type
		for x in range(room.x1, room.x2 + 1):
			for y in range(room.y1, room.y2 + 1):
				self.map_grid[x][y].set_type('floor')

		self.rooms.append(room)

	def create_vert_line(self, x, y1, y2):
		"carve vertical tunnel"
		for y in range(min(y1, y2), max(y1, y2) + 1):
			self.map_grid[x][y].set_type('floor')
	 
	def create_vert_line_up(self, x, y):
		"carve vertical tunnel from point and up"
		while y > 0 and not self.map_grid[x][y].walkable:
			self.map_grid[x][y].set_type('floor')
			y -= 1
	 
	def create_vert_line_down(self, x, y):
		"carve vertical tunnel from point and down"
		while y < MAP_HEIGHT and not self.map_grid[x][y].walkable:
			self.map_grid[x][y].set_type('floor')
			y += 1
	 
	def create_hor_line(self, y, x1, x2):
		"carve horizontal tunnel"
		for x in range(min(x1, x2), max(x1, x2) + 1):
			self.map_grid[x][y].set_type('floor')
	 
	def create_hor_line_left(self, x, y):
		"carve horizontal tunnel from point and left"
		while x > 0 and not self.map_grid[x][y].walkable:
			self.map_grid[x][y].set_type('floor')
			x -= 1
	 
	def create_hor_line_right(self, x, y):
		"carve horizontal tunnel from point and right"
		while x < MAP_WIDTH and not self.map_grid[x][y].walkable:
			self.map_grid[x][y].set_type('floor')
			x += 1

	def choose_starting_room(self):
		"randomly choose the index of the room, where player will be placed"
		self.starting_room = random.choice(self.rooms)
		

class Rectangle:
	"a rectangle on the map, used to characterize a room"
	def __init__(self, x, y, width, height):
		"create new room with certain coordinates and dimensions"
		#top-left corner
		self.x1 = x
		self.y1 = y
		#bottom-right corner
		self.x2 = x + width
		self.y2 = y + height
		
	def center(self):
		"returns coordinates of the center of this room"
		center_x = (self.x1 + self.x2) / 2
		center_y = (self.y1 + self.y2) / 2
		return (center_x, center_y)
		
	def intersect(self, other):
		"returns True if two rooms intersect"
		return (self.x1 <= other.x2 and self.y1 <= other.y2 and self.x2 >= other.x1 and self.y2 >= other.y1)



