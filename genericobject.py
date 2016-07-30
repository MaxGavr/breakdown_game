from math import sqrt
import libtcodpy as libtcod
from interface import to_camera_coordinates

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# Object
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

class Object:
	"""
		this is a generic object: the player, any other character, an item, the stairs...
		it's always represented by a character on screen and hold methods, related to its visualising
	"""
	def __init__(self, tile, char, color, name, blocks_path = False, always_visible = False):
		"create new object"
		self.pos = tile #reference to Tile instance, the position of object
		self.icon = char #text character, representing this object
		self.color = color #color of text character
		self.name = name #obvious
		self.blocks_path = blocks_path #indicates, whether this object makes the tile it is on impassable
		if self.blocks_path:
			self.pos.occupied = True
		self.always_visible = always_visible #if True, the object is drawn even if it is not in the player's FOV (the only condition is to reside on explored tile)
		
	def distance_to(self, other):
		"return distance to another object"
		dx = other.pos.x - self.pos.x
		dy = other.pos.y - self.pos.y
		return sqrt(dx ** 2 + dy ** 2)

	def distance(self, x, y):
		"return distance to some coordinates"
		return sqrt((x - self.pos.x) ** 2 + (y - self.pos.y) ** 2)

	def is_here(self, x, y):
		"check if object is situated at the point (x, y)"
		if self.pos.x == x and self.pos.y == y:
			return True
		else:
			return False
	
	def draw(self, camera_pos, console):
		"draw the character that represents this object at its position"
		(x, y) = to_camera_coordinates(camera_pos, self.pos.x, self.pos.y)
		if x is not None:
			if self.pos.is_in_fov or (self.always_visible and self.pos.explored):
				libtcod.console_put_char_ex(console, x, y, self.icon, self.color, libtcod.BKGND_DEFAULT)
		
	def clear(self, camera_pos, console):
		"erase the character that represents this object"
		(x, y) = to_camera_coordinates(camera_pos, self.pos.x, self.pos.y)
		if x is not None:
			libtcod.console_put_char(console, x, y, ' ')


