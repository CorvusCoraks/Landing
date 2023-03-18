""" Настройки проекта. """
from torch.nn import Sequential, Sigmoid, Linear
from typing import List, Dict, Any
from nn_iface.norm import MinMaxXY, MinMax, MinFloat, MaxFloat
from basics import GRAVITY_ACCELERATION_ABS
from math import pi

ACTOR_INPUT: List = [Sigmoid()]
ACTOR_HIDDEN: List = [Linear(9, 9, bias=False), Sigmoid()]
ACTOR_OUTPUT: List = [Linear(9, 5, bias=False), Sigmoid()]
# Full options list see in NetSeq class init()
# ACTOR_OPTIONS: Dict[str, Any] = {'initMethod': nn.init.orthogonal_, 'initWeights': True}
ACTOR_OPTIONS: Dict[str, Any] = {'initWeights': True}

CRITIC_INPUT: List = [Sigmoid()]
CRITIC_HIDDEN: List = [Linear(14, 14, bias=False), Sigmoid()]
CRITIC_OUTPUT: List = [Linear(14, 1, bias=False), Sigmoid()]
CRITIC_OPTIONS: Dict[str, Any] = {'initWeights': True}

POSITION_MINMAX: MinMaxXY = MinMaxXY(MinMax(-100.0, 100.0), MinMax(-10.0, 500.0))
LINE_VELOCITY_MINMAX: MinMaxXY = MinMaxXY(MinMax(-100.0, 100.0), MinMax(-100.0, 100.0))
LINE_ACCELERATION_MINMAX: MinMaxXY = MinMaxXY(MinMax(-10.0 * GRAVITY_ACCELERATION_ABS, 10.0 * GRAVITY_ACCELERATION_ABS),
                                              MinMax(-10.0 * GRAVITY_ACCELERATION_ABS, 10.0 * GRAVITY_ACCELERATION_ABS))

ORIENTATION_MINMAX: MinMax = MinMax(-pi, pi)
ANGULAR_VELOCITY_MINMAX: MinMax = MinMax(-pi / 18, pi / 18)
ANGULAR_ACCELERATION_MINMAX: MinMax = MinMax(-pi / 180, pi / 180)

NN_STORAGE_FILENAME: str = '/nn.pt'
STATE_STORAGE_FILENAME: str = '/state.pt'
