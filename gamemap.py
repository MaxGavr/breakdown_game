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

	def place_enemies(self):
		"fill the station level with enemies"
		local_map = self.level_map.map_grid
		for room in self.level_map.rooms:
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
			return None
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
	def __init__(self, map_width = MAP_WIDTH, map_height = MAP_HEIGHT):
		"create blank map and fill it with rooms"
		#fill map with impassable tiles
		self.map_grid = [ [Tile(x, y, 'wall') for y in range(map_height)] for x in range(map_width) ]

		#rooms of the current map, presented as instances of 'Rectangle' class
		self.rooms = []

		#randomly fill the level with rooms, connected via one-tile corridors
		for r in range(MAX_ROOMS):
			#generate new room as the rectangle with random position and sizes
			width = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
			height = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
			x = libtcod.random_get_int(0, 0, map_width - width - 1)
			y = libtcod.random_get_int(0, 0, map_height - height - 1)
			new_room = Rectangle(x, y, width, height)
			failed = False
			
			#check if rooms intersect
			for other_room in self.rooms:
				if new_room.intersect(other_room):
					failed = True
					break
			
			#connect rooms with corridors
			if not failed:
				self.create_room(new_room)
				(new_x, new_y) = new_room.center()
				
				if len(self.rooms) > 0:
					(prev_x, prev_y) = self.rooms[len(self.rooms)-2].center()
					if libtcod.random_get_int(0, 0, 1):
						self.create_hor_tunnel(prev_x, new_x, prev_y)
						self.create_vert_tunnel(prev_y, new_y, new_x)
					else:
						self.create_vert_tunnel(prev_y, new_y, prev_x)
						self.create_hor_tunnel(prev_x, new_x, new_y)

	def create_room(self, room):
		"carve rectangle room"
		#go through the tiles in the rectangle and make them passable by changing their type
		for x in range(room.x1 + 1, room.x2):
			for y in range(room.y1 + 1, room.y2):
				self.map_grid[x][y].set_type('floor')

		self.rooms.append(room)

	def create_vert_tunnel(self, y1, y2, x):
		"carve vertical tunnel"
		for y in range(min(y1, y2), max(y1, y2) + 1):
			self.map_grid[x][y].set_type('floor')

	def create_hor_tunnel(self, x1, x2, y):
		"carve horizontal tunneln"
		for x in range(min(x1, x2), max(x1, x2) + 1):
			self.map_grid[x][y].set_type('floor')

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



