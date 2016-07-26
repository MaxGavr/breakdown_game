from genericobject import Object
from AI import ConfusedAI
from interface import target_tile, target_enemy, is_targetable
from globs import *

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# Item, Equipment
# Contains functions and globals, connected to items/equipment and its using
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

class Item(Object):
	"""
		an item that can be picked up and (probably) used
		unlike Character, it doesn't have any information about the level, except its own position (single tile)
	"""
	def __init__(self, tile, char, color, name, use_function = None, disposable = True, equipment = None, owner = None):
		"create new item"
		Object.__init__(self, tile, char, color, name, blocks_path = False, always_visible = True)
		
		self.use_function = use_function #function, that is called when item is used
		self.disposable = disposable #indicates, if an is destroyed after single use
		
		self.owner = owner #reference to the Character instance that carries this item
		if self.owner is not None:
			self.owner.inventory.append(self)

		self.equip_unit = equipment #Equipment instance, if this item is a piece of equipment
		if self.equip_unit is not None:
			self.equip_unit.owner = self

	def use(self, game):
		"call use_function of this item, if it exists"
		#indicates if the item is going to be used by the player
		owner_is_player = True if 'state' in self.owner.__dict__ else False
		
		if self.use_function is not None:
			result = self.use_function(game)
			if result != 'cancelled':
				if self.disposable: self.owner.inventory.remove(self)
				#change the state of player, who carries this item
				if owner_is_player:
					self.owner.state = 'acted'
			else:
				game.log.message("Okay, than...", libtcod.grey)
				if owner_is_player:
					self.owner.state = 'idle'
		else:
			game.log.message("The " + self.name + " can't be used.")
			if owner_is_player:
				self.owner.state = 'acted'
	
	def pick_up(self, log, character, level_items):
		"add an item to the inventory and remove from the map"
		if len(character.inventory) >= MAX_INVENTORY_SIZE:
			log.message('Your inventory is full, cannot pick up the' + self.name + '.', libtcod.darker_red)
			if 'state' in self.owner.__dict__:
				self.owner.state = 'idle'
		else:
			character.add_item(self)
			level_items.remove(self)
			log.message('You picked up a ' + self.name + '!', libtcod.green)	
			if 'state' in self.owner.__dict__:
				self.owner.state = 'acted'

	def drop(self, log, level_items):
		"add an item to the map and remove from the character's inventory, place it at the character's coordinates"
		self.owner.inventory.remove(self)
		level_items.append(self)
		self.pos = self.owner.pos

		if 'state' in self.owner.__dict__:
			self.owner.state = 'acted'
		self.owner = None
		
		log.message('You dropped a ' + self.name + '.', libtcod.yellow)
		

class Equipment:
	"""
		contains functions, related to equippable items
	"""
	def __init__(self, slot):
		"create ne Environment instance"
		self.slot = slot #represents the role of this item, serves as keyword in Character's equipment'

	def equip(self):
		"put on this part of equipment"
		if self.owner.owner is not None:
			if self.owner.owner.equipment[self.slot] is not None:
				self.owner.owner.equipment[self.slot].unequip()
		self.owner.owner.equipment[self.slot] = self
	
	def unequip(self):
		"unequip this part of equipment"
		if self.owner.owner is not None:
			self.owner.owner.equipment[self.slot] = None

	def is_equipped(self):
		"check if this part of equipment is actually weared by character"
		if self.owner.owner is not None:
			if self.owner.owner.equipment[self.slot] == self:
				return True
			else:
				return False

def generate_item(item_id):
	"construct Item instance using item type ID"
	item = ITEM_DICT[item_id] #explanation below
	
	if item['equip'] is None:
		new_item = Item(None, item['icon'], item['color'], item['name'], item['use'], item['disposable'])
	else:
		equip = Equipment(item['equip'])
		new_item = Item(None, item['icon'], item['color'], item['name'], item['use'], item['disposable'], equip)

	return new_item

def add_item_to_char(char, item_id):
	"generate new item and place add it to the character's inventory"
	item = generate_item(item_id)
	char.add_item(item)

def add_item_to_lvl(station_level, x, y, item_id):
	"generate new item and place add it on the map"
	item = generate_item(item_id)
	item.pos = station_level.level_map.map_grid[x][y]
	station_level.items.append(item)

##########################################################
# Item use functions
##########################################################

def item_stimulator(game):
	"heal the player"
	if game.player.fighter.hp == game.player.fighter.max_hp:
		game.log.message("You don't have any injuries to take care of.", libtcod.lighter_green)
		return 'cancelled'

	game.log.message('Your wounds start to fell better!', libtcod.light_violet)
	game.player.fighter.heal(STIM_HEAL_AMOUNT)

def item_discharge(game):
	"find closest enemy and damage it with electric discharge"
	enemy = game.location.closest_enemy(game.player, ITEM_USING_RANGE)
	if enemy is None:
		game.log.message('No enemy close enough to strike.', libtcod.dark_red)
		return 'cancelled'

	game.log.message('An electric discharge strikes the ' + enemy.name + ' with a loud crack! The damage is ' + str(DISCHARGE_DAMAGE) + ' hit points.', libtcod.light_blue)
	enemy.fighter.take_damage(game, DISCHARGE_DAMAGE)

def item_modulator(game):
	"confuse an enemy, chosen by mouse click"
	game.log.message("Choose an enemy to break it's behavioral unit (right-click to cancel).", libtcod.light_cyan)
	enemy = target_enemy(game, ITEM_USING_RANGE)
	if enemy is None:
		return 'cancelled'

	else:
		#replace the enemy's AI with a "confused" one; after some turns it will restore the old AI
		old_ai = enemy.ai
		enemy.ai = ConfusedAI(old_ai)
		enemy.ai.owner = enemy
		game.log.message('The metal eyes of the ' + enemy.name + ' stop glowing, as he starts to stumble around!', libtcod.light_green)

def item_grenade(game):
	"throw grenade at the location, where player clicked"
	game.log.message('Choose a place to throw a grenade at (right-click to cancel).', libtcod.light_cyan)
	(x, y) = target_tile(game)
	if x is None: return 'cancelled'
	game.log.message('The grenade explodes, damaging electronics within ' + str(GRENADE_RADIUS) + ' tiles!', libtcod.orange)

	#find enemies in the affected area and damage them
	for char in game.location.characters:
		if char.distance(x, y) <= GRENADE_RADIUS and char.fighter:
			game.log.message('The ' + char.name + ' takes ' + str(GRENADE_DAMAGE) + ' damage.', libtcod.orange)
			char.fighter.take_damage(game, GRENADE_DAMAGE)

def weapon_laser(game):
	"""
		shoot an enemy with your laser weapon
		use_function for laser weapons
	"""
	enemy = target_enemy(game, WEAPON_RANGE)
	if enemy is not None:
		if is_targetable(game.player, enemy):
			weapon = game.player.equipment['weapon'].owner.name
			if weapon == 'laser rifle':
				damage = LASER_RIFLE_DAMAGE
			elif weapon == 'laser pistol':
				damage = LASER_PISTOL_DAMAGE
			game.log.message("You shoot " + enemy.name + " with your " + weapon + " dealing " + str(LASER_PISTOL_DAMAGE) + " damage.", libtcod.pink)
			enemy.fighter.take_damage(game, damage)
		else:
			game.log.message(enemy.name + ' is inaccessible from here.', libtcod.lighter_red)
			return 'cancelled'
	else: return 'cancelled'

##########################################################

#possible item types
#some properties description:
#	'use' - function that is called when item is used
#	'disposable' - True if item can be used only once
#	'equip' - slot for item's Equipment instance
#
#current items: 'stimulator', 'discharge generator', 'impulse grenade', 'behavioral modulator', 'remains of robo-miner' and 'robo-guard', 'laser rifle', 'laser pistol'
#
#in order to add new item, just create additional dict holding its properties as shown below and append it to 'TYLE_TYPES'
#'item_id' used in 'generate_item' is an index of an item in 'ITEM_DICT'

stimulator = {'icon': '!', 'color': libtcod.pink, 'name': 'stimulator', 'use': item_stimulator, 'disposable': True, 'equip': None}
discharge = {'icon': '#', 'color': libtcod.cyan, 'name': 'discharge generator', 'use': item_discharge, 'disposable': True, 'equip': None}
grenade = {'icon': '#', 'color': libtcod.red, 'name': 'impulse grenade', 'use': item_grenade, 'disposable': True, 'equip': None}
modulator = {'icon': '#', 'color': libtcod.green, 'name': 'behavioral modulator', 'use': item_modulator, 'disposable': True, 'equip': None}
miner_r = {'icon': '%', 'color': libtcod.dark_red, 'name': 'remains of robo-miner', 'use': None,  'disposable': False, 'equip': None}
guard_r = {'icon': '%', 'color': libtcod.dark_red, 'name': 'remains of robo-guard', 'use': None,  'disposable': False, 'equip': None}
l_rifle = {'icon': ')', 'color': libtcod.dark_blue, 'name': 'laser rifle', 'use': weapon_laser, 'disposable': False, 'equip': 'weapon'}
l_pistol = {'icon': ')', 'color': libtcod.light_blue, 'name': 'laser pistol', 'use': weapon_laser, 'disposable': False, 'equip': 'weapon'}

ITEM_DICT = (stimulator, discharge, grenade, modulator, miner_r, guard_r, l_rifle, l_pistol)
