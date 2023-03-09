""" Config string constants (string keys in configuration dicts). """

# ─┐
#  ├─ R_PROJECT_NAME_BLOCK
#  │   ├── PROJECT_NAME
#  │
#  ├─ R_NEURONNET
#  │   ├── ACTOR_BLOCK
#  │   │   ├── SIZE (на фиг, всё в блоке LAYERS)
#  │   │   ├── LAYERS
#  │   │       ├── INPUT
#  │   │       │       ├── NEURONS_COUNT
#  │   │       │       ├── ACTIVATION
#  │   │       │
#  │   │       ├── SEQUENCES
#  │   │       │   ├── 0
#  │   │       │   │   ├── NEURONS_COUNT
#  │   │       │   │   ├── REPEAT_COUNT
#  │   │       │   │   ├── CHANNEL_TYPE
#  │   │       │   │   ├── ACTIVATION_TYPE
#  │   │       │   │
#  │   │       │   ├── 1
#  │   │       │       ├── NEURONS_COUNT
#  │   │       │       ├── REPEAT_COUNT
#  │   │       │       ├── CHANNEL_TYPE
#  │   │       │       ├── ACTIVATION_TYPE
#  │   │       │
#  │   │       ├── OUTPUT
#  │   │               ├── NEURONS_COUNT
#  │   │               ├── CHANNEL_TYPE
#  │   │               ├── ACTIVATION_TYPE
#  │   │
#  │   ├── CRITIC_BLOCK
#  │       ├── structure similar of ACTOR_BLOCK
#  │
#  ├─ R_STORAGE_BLOCK
#  │   ├── STORAGE_FILE_BLOCK
#  │   │   ├── NEURONNET_FILE
#  │   │   ├── TRANING_STATE_FILE
#  │   │
#  │   ├── other storage strings keys block
#  │
#  ├─ R_INPUT_NORMALIZATION
#      ├── MINMAX_BLOCK
#      │   ├─── LINEAR_BLOCK
#      │   │   ├─── POSITION
#      │   │   ├─── VELOCITY
#      │   │   ├─── ACCELERATION
#      │   │
#      │   ├─── ANGULAR_BLOCK
#      │       ├─── ORIENTATION
#      │       ├─── VELOCITY
#      │       ├─── ACCELERATION
#      │
#      ├── other input normalization strings keys block

########################
########################
########################
# Root block constants.
R_PROJECT_NAME_BLOCK = 'ProjectName'
R_NEURONNET = 'NeuronNet'
R_STORAGE_BLOCK = 'Storage'
R_INPUT_NORMALIZATION = 'Normalisation'

########################
########################
########################
# R_PROJECT_NAME_BLOCK constants.
PROJECT_NAME = 'name'

########################
# R_NEURONNET sub blocks.
ACTOR_BLOCK = 'Actor'
CRITIC_BLOCK = 'Critic'

########################
# R_STORAGE_BLOCK sub blocks.
STORAGE_FILE_BLOCK = 'File'

########################
# R_INPUT_NORMALIZATION sub blocks.
MINMAX_BLOCK = 'MinMax'

########################
########################
########################
# STORAGE_FILE_BLOCK constants.
########################
NEURONNET_FILE = 'neuron_net'
TRANING_STATE_FILE = 'traning_state'

########################
# Neuron nets sequences constants.
# sequence inputs count (int)
NEURONS_COUNT = 'inputs'
# sequence repeat count (int)
REPEAT_COUNT = 'count'
# sequence input type (Linear etc.)
CHANNEL_TYPE = 'channal'
# sequence activation (Sigmoid etc.)
ACTIVATION_TYPE = 'activation'






#############################
# Common neuron net constants
SIZE_BLOCK = 'Size'
INPUT = 'input'
HIDDEN = 'hidden'
# if that key present, LAYER_BLOCK section ignored (?)
LAYERS = 'layers'
OUTPUT = 'output'
############################

LAYERS_BLOCK = 'Layers'
############################
# Layers subblocks
INPUT_BLOCK = 'Input'
HIDDEN_BLOCK = 'Hidden'
OUTPUT_BLOCK = 'Output'
###########################


# List with layers in one "brick"
# Example toml: layers = ['Linear', 'Sigmoid']
SEQUENCE_LIST = 'layers'
# "Brick" repeat count
SEQUENCE_COUNT = 'count'
