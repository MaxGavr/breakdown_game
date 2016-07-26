import libtcodpy as libtcod
from globs import MESSAGE_WIDTH, MESSAGE_HEIGHT, MESSAGE_X
from textwrap import wrap

#-----------------------------
#~~~~~~~~~~~~~~~~~~~~~~~
# GameLog
# May contain handling text output
#~~~~~~~~~~~~~~~~~~~~~~~
#-----------------------------

class GameLog:
	"""
		general class, that contains all in-game text input
		for now it's just simple multiline message log, that can hold few (5 or so) lines of text
	"""
	def __init__(self):
		"create blank log"
		self.messages = [] #various in-game messages, presented by tuples (text, color)

	def message(self, msg, color = libtcod.white):
		"add new message to the game's log"
		#split the message if necessary, among multiple lines
		msg_lines = wrap(msg, MESSAGE_WIDTH)

		for line in msg_lines:
			#if the buffer is full, remove the first line to make room for the new one
			if len(self.messages) == MESSAGE_HEIGHT:
				del self.messages[0]

			#add the new line as the tuple, with the text and the color
			self.messages.append( (line, color) )

	def display_messages(self, console):
		"print the game messages, one line at a time"
		y = 1
		for (line, color) in self.messages:
			libtcod.console_set_default_foreground(console, color)
			libtcod.console_print_ex(console, MESSAGE_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
			y += 1

