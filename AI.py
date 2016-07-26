from globs import *

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# BasicAI, ConfusedAI
# Here should lie everything related to NPC behaviour
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

#following AIs are very primitive and should be improved

class BasicAI:
	"""
		AI for a basic enemy
		behaviour is simple: once in character is in the player's FOV it move towards him and beat him up
		it can be improved by using character's FOV instead of only player's FOV
	"""
	def take_turn(self, game, player):
		"go to the player and beat him up"
		enemy = self.owner
		if enemy.pos.is_in_fov:

			#if the player is to far away - chase him
			if enemy.distance_to(player) >= 2:
				enemy.move_astar(player)

			#if he is near - attack him
			elif player.fighter.hp > 0:
				enemy.fighter.attack(game, player)

class ConfusedAI:
	"""
		AI for a temporarily confused enemy (reverts to previous AI after a while)
		just randomly fooling around for a few turns
	"""
	def __init__(self, old_ai, num_turns = CONFUSE_TURNS):
		"initialize new AI"
		self.old_ai = old_ai #previous character's AI, it will be restored after several turns
		self.turns = num_turns #number of turns enemy is being confused

	def take_turn(self, game, player):
		"move in a random direction, ignoring player and everything"
		if self.turns > 0:
			dx = libtcod.random_get_int(0, -1, 1)
			dy = libtcod.random_get_int(0, -1, 1)
			self.owner.move(dx, dy)
			self.turns -= 1

		else:
			self.owner.ai = self.old_ai
			game.log.message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)
