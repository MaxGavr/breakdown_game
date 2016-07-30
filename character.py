from genericobject import Object, sqrt
import AI
from item import add_item_to_lvl
from globs import *

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# Character, Player, Fighter
# Contains functions, that deal with spawning, generating characters and player, and various events related to their existence
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

class Character(Object):
	"""
		class derived from Object, representing any in-game character (excluding player)
		unlike Object instances, characters can move, attack and have access to the map
		every character possesses its own FOV map
	"""
	def __init__(self, tile, map, char, color, name, fighter, ai = None):
		"create new character"
		Object.__init__(self, tile, char, color, name, blocks_path = True, always_visible = False)

		self.entire_map = map #GameMap instance, map of the current level

		self.fighter = fighter #Fighter instance
		self.fighter.owner = self #create the reference to this character from its own Fighter component

		self.ai = ai #on of the AIs instance
		if self.ai:
			self.ai.owner = self

		self.inventory = [] #list of items, that this character carries
		self.equipment = {'weapon': None, 
						  'armor': None} #equipment, matters only to the player

		self.init_fov() #compute personal FOV for this character

	def init_fov(self):
		"generate FOV map for this character"
		self.fov_recompute = True #indicates, if FOV should be recomputed; changes to True when character moves

		#create FOV map, according to the level map
		self.fov = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
		for x in range(MAP_WIDTH):
			for y in range(MAP_HEIGHT):
				libtcod.map_set_properties(self.fov, x, y, self.entire_map[x][y].transparent, not self.entire_map[x][y].is_blocked())

	def compute_fov(self): #for now this function is used only in the Player's 'compute_fov, but it can come in handy when redoing current enemies detecting system'
		"calculate FOV for this character, perform"
		if self.fov_recompute:
			self.fov_recompute = False
			libtcod.map_compute_fov(self.fov, self.pos.x, self.pos.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

	def move(self, dx, dy):
		"""
			move by the given amount, if the destination is not blocked
			returns True if movement was successfull, False if it wasn't
		"""
		destination = self.entire_map[self.pos.x + dx][self.pos.y + dy]
		if not destination.is_blocked():
			self.pos.occupied = False
			self.pos = destination
			if self.blocks_path:
				self.pos.occupied = True
			self.fov_recompute = True
			return True
			
		else:
			return False

	def move_towards(self, target_x, target_y):
		"move towards certain point, destination is calculated on the fly"
		dx = target_x - self.pos.x
		dy = target_y - self.pos.y
		distance = sqrt(dx ** 2 + dy ** 2) #as simple, as it is

		dx = int(round(dx / distance))
		dy = int(round(dy / distance))
		self.move(dx, dy)

	def move_astar(self, target): #it is not perfect, but it really works
		"perform move towards 'target' using A* pathfinding algorithm"
		#description can be found in 'python+libtcod roguelike' article
		path = libtcod.path_new_using_map(self.fov, 1.41)

		libtcod.path_compute(path, self.pos.x, self.pos.y, target.pos.x, target.pos.y)

		if not libtcod.path_is_empty(path) and libtcod.path_size(path) < 25:
			x, y = libtcod.path_walk(path, True)
			if x or y:
				self.move(x - self.pos.x, y - self.pos.y)
		else:
			self.move_towards(target.pos.x, target.pos.y)

		libtcod.path_delete(path)

	def add_item(self, item):
		"add an item to the characters inventory"
		if len(self.inventory) < MAX_INVENTORY_SIZE:
			self.inventory.append(item)
			item.owner = self
			item.pos = None

class Fighter:
	"""
		combat-related properties and methods for characters
		they are placed in the separate class in order to prevent Character of being too bulky
	"""
	def __init__(self, hp, defense, power, exp = 0, death_function = None):
		"create new Fighter instance, everything is obvious"
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power
		self.exp = exp #for now it is not used anywhere
		self.death_function = death_function
		#every Fighter instance also hold reference to the Character instance, that it is connected with
		#it can be accessed by 'self.owner' (see Character.__init__)
		

	def take_damage(self, game, damage):
		"reduces character's health by some value; call 'death_function' upon character's death"
		if damage > 0:
			self.hp -= damage

			if self.hp <= 0:
				if self.death_function is not None:
					self.death_function(game, self.owner)

	def heal(self, amount):
		"increase character's health by some value"
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp

	def attack(self, game, target): #primitive damage-calculating scheme should be redone completely
		"one character attacks another"
		damage = self.power - target.fighter.defense

		if damage > 0:
			game.log.message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points!')
			target.fighter.take_damage(game, damage)
		else:
			game.log.message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

class Player(Character):
	"class that represents unique character - player"
	def __init__(self, tile, map, char, color, name, fighter):
		"construct Player instance"
		Character.__init__(self, tile, map, char, color, name, fighter)
		"""
			player's state indicator; possible states: 'idle' and 'acted'
		"""
		self.state = None

	def move_or_attack(self, game, dx, dy):
		"perform movement or attack in the specific direction"

		#destination coordinates
		x = self.pos.x + dx
		y = self.pos.y + dy

		target = None
		for char in game.location.characters:
			if char.is_here(x, y):
				target = char
				break

		if target is not None:
			self.fighter.attack(game, target)
			self.state = 'acted'
		else:
			if self.move(dx, dy):
				self.state = 'acted'
			else:
				game.log.message("You can't go there.", libtcod.light_grey)
				self.state = 'idle'

	def compute_fov(self):
		"similar to character's 'compute_fov', but also marks all visible tiles: tile.is_in_fov = True"
		if self.fov_recompute:
			self.fov_recompute = False
			libtcod.map_compute_fov(self.fov, self.pos.x, self.pos.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
			
			for y in range(MAP_HEIGHT):
				for x in range(MAP_WIDTH):
					visible = libtcod.map_is_in_fov(self.fov, x, y)
					if visible: #tile is in the player's FOV
						self.entire_map[x][y].explored = True
						self.entire_map[x][y].is_in_fov = True
					else:
						self.entire_map[x][y].is_in_fov = False



def enemy_death(game, char):
	"the event of enemy's death"
	game.log.message(char.name.capitalize() + ' is dead!', libtcod.orange)
	char.pos.occupied = False

	#place character's remains on his last position
	if char.name == 'robo-miner':
		add_item_to_lvl(game.location, char.pos.x, char.pos.y, 4)
	elif char.name  == 'robo-guard':
		add_item_to_lvl(game.location, char.pos.x, char.pos.y, 5)

	game.location.characters.remove(char)
	del char

def player_death(game, player): #too simple
	"the event of player's death"
	game.log.message('As your vision fades, you suddenly understand - your death has come...', libtcod.red)
	game.game_state = 'dead'

	player.icon = '%'
	player.color = libtcod.dark_red

def generate_enemy(station_level, x, y, char_id):
	"construct Character instance using character's ID and place it on the map"
	local_map = station_level.level_map.map_grid
	
	char = CHAR_DICT[char_id] #explanations below
	fighter_component = Fighter(char['hp'], char['def'], char['pow'], char['exp'], char['death'])
	ai_component = char['ai']()
	enemy = Character(local_map[x][y], local_map, char['icon'], char['color'], char['name'], fighter_component, ai_component)
	
	station_level.characters.append(enemy)

def generate_player(station_level, x, y):
	"construct Player instance and put it on the map"
	local_map = station_level.level_map.map_grid
	
	player_fighter_component = Fighter(hp = 150, defense = 5, power = 20, death_function = player_death)
	player = Player(local_map[x][y], local_map, '@', libtcod.white, 'hero', player_fighter_component)

	return player


# possible characters
# some properties description:
#	'death' is a function that is called when character dies
#	'ai' is an AI.* instance
#
#current characters: 'robo-guard' and 'robo-miner'
#
#in order to add new character, just create additional dict holding its properties as shown below and append it to 'CHAR_DICT'
#
#'char_id' used in 'generate_enemy' is an index of a character in 'CHAR_DICT'

miner = {'hp': 50, 'def': 0, 'pow': 10, 'exp': 25, 'death': enemy_death, 'ai': AI.BasicAI,
		 'icon': 'm', 'color': libtcod.light_cyan, 'name': 'robo-miner'}
guard = {'hp': 75, 'def': 5, 'pow': 20, 'exp': 100, 'death': enemy_death, 'ai': AI.BasicAI,
		 'icon': 'G', 'color': libtcod.darkest_han, 'name': 'robo-guard'}

CHAR_DICT = (miner, guard)
