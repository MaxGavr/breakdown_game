import libtcodpy as libtcod
#globs are imported almost everywhere, so unnecessary libtcod imports should be omitted

##########################################################
# Options
##########################################################
#it's better to pack them into separate file

LIMIT_FPS = 20

#size of the map
MAP_WIDTH = 100
MAP_HEIGHT = 80

#size of the camera screen
CAMERA_WIDTH = 80
CAMERA_HEIGHT = 43

#size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

#map generating settings
MAX_ROOM_ENEMIES = 3
MAX_ROOM_ITEMS = 3
#BSP options
DEPTH = 10 #number of node splittings
ROOM_MIN_SIZE = 6
FULL_ROOMS = False

#sizes and coordinates for GUI
PANEL_HEIGHT = 7
BAR_WIDTH = 20
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MESSAGE_X = BAR_WIDTH + 2
MESSAGE_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MESSAGE_HEIGHT = PANEL_HEIGHT - 1

#inventory properties
MAX_INVENTORY_SIZE = 26
INVENTORY_WIDTH = 50

#item properties
STIM_HEAL_AMOUNT = 50
DISCHARGE_DAMAGE = 100
ITEM_USING_RANGE = 5
CONFUSE_TURNS = 10
GRENADE_DAMAGE = 30
GRENADE_RADIUS = 3

#weapon properties
WEAPON_RANGE = 5
LASER_PISTOL_DAMAGE = 20
LASER_RIFLE_DAMAGE = 50

#experience properties
LEVEL_UP_BASE = 100
LEVEL_UP_FACTOR = 150

#FOV properties
FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

##########################################################

#colors of invisible tiles
c_hid_wall = libtcod.Color(22, 7, 115)
c_hid_floor = libtcod.Color(55, 46, 133)
#colors of visible tiles 
c_vis_wall = libtcod.Color(148, 122, 23)
c_vis_floor = libtcod.Color(180, 155, 58)
#colors of highlighted tiles
c_hi_wall = libtcod.Color(67, 128, 211)
c_hi_floor = libtcod.Color(105, 150, 211)

#possible tile types
#properties description:
#	title - just a name for a specific terrain, also used as key for a corresponding tile type in 'TYLE_TYPES' dict
#	walkable - indicates, if tiles of this type can hold an object (character, item and so on) on the top of itself
#	transparent - indicates, whether the tile blocks line of sight during calculating FOV for characters or not
#	vis_color, hid_color, hi_color - visible color, hidden color, highlighted color respectively; used in 'calculate_color' function
#
#current types: 'floor', 'wall'
#
#in order to add new type, just create additional dict holding its properties as shown below and append it to 'TYLE_TYPES'
#'tile_type' used in 'Tile.set_type' is the keyword of a corresponding type in 'TILE_TYPES'

floor = {'title': 'f1loor', 'walkable': True, 'transparent': True, 'vis_color': c_vis_floor, 'hid_color': c_hid_floor, 'hi_color': c_hi_floor}
wall = {'title': 'metal wall', 'walkable': False, 'transparent': False, 'vis_color': c_vis_wall, 'hid_color': c_hid_wall, 'hi_color': c_hi_wall}
TILE_TYPES = {'floor': floor, 'wall': wall}

#variables for input handling
#they are kept here, as they don't hold any used information outside input-handling functions
#it doesn't matter, if they are constantly reinitializing
key = libtcod.Key()
mouse = libtcod.Mouse()

##########################################################
