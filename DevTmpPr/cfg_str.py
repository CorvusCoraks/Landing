""" Config strings constants (keys in configuration dicts). """
# String keys in this file complementing main config strings (keys) constants file cfgconst.py.
from cfgconst import R_INPUT_NORMALIZATION

# if subsection is not dict, that is - ending string-key

# Linear block (position, velocity, acceleration) min-max
# Toml exapmle: x = [-100.0, 100.0]
X_MINMAX_LIST = 'x'
Y_MINMAX_LIST = 'y'

# Angular block min-max
# Toml exapmle: orientation = [-100.0, 100.0]
ORIENTATION = 'orientation'
VELOCITY = 'velocity'
ACCELERATION = 'acceleration'

# Normalisation linear subsections
POSITION_BLOCK = 'Position'
# This block subsections (or key strings)
POSITION_STRUCTURE = {POSITION_BLOCK: [X_MINMAX_LIST, Y_MINMAX_LIST]}
VELOCITY_BLOCK = 'Velocity'
# This block subsections (or key strings)
VELOCITY_STRUCTURE = {VELOCITY_BLOCK: [X_MINMAX_LIST, Y_MINMAX_LIST]}
ACCELERATION_BLOCK = 'Acceleration'
# This block subsections (or key strings)
ACCELERATION_STRUCTURE = {ACCELERATION_BLOCK: [X_MINMAX_LIST, Y_MINMAX_LIST]}

# Linear sub section
LINEAR_BLOCK = 'Linear'
# This block subsections (or key strings)
LINEAR_STRUCTURE = {LINEAR_BLOCK: [POSITION_STRUCTURE, VELOCITY_STRUCTURE, ACCELERATION_STRUCTURE]}

# Angular sub section
ANGULAR_BLOCK = 'Angular'
# This block subsections (or key strings)
ANGULAR_STRUCTURE = {ANGULAR_BLOCK: [ORIENTATION, VELOCITY, ACCELERATION]}

# Subsection for min-max normalization strings in config
MINMAX_BLOCK = 'MinMax'
# This block subsections (or key strings)
MINMAX_STRUCTURE = {MINMAX_BLOCK: [LINEAR_STRUCTURE, ANGULAR_STRUCTURE]}

# Position in main config section
POSITION_IN_CONFIG = {R_INPUT_NORMALIZATION: [MINMAX_STRUCTURE]}
