""" Настройки проекта. """
from torch.nn import Sequential, Sigmoid, Linear
import torch.optim
from typing import List, Dict, Any, Type
from nn_iface.norm import MinMaxXY, MinMax, MinFloat, MaxFloat
from nn_iface.ifaces import LossCriticInterface
from basics import GRAVITY_ACCELERATION_ABS
from math import pi
from nn_iface.projects import MSE_RLLoss, MSELoss, LossActorInterface, LossCriticInterface

ACTOR_INPUT: List = [Sigmoid()]
ACTOR_HIDDEN: List = [Linear(9, 9, bias=False), Sigmoid()]
ACTOR_OUTPUT: List = [Linear(9, 5, bias=False), Sigmoid()]
# Full options list see in NetSeq class __init__()
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

# Количество реактивных двигателей изделия.
JETS_COUNT: int = 5

# Постоянный шаг.
ALPHA: float = 0.001
# Коэф. приведения 0<=gamma<=1
GAMMA: float = 0.001

# Класс ошибки актора
ACTOR_LOSS: type[LossActorInterface] = MSELoss
# Класс ошибки критика.
CRITIC_LOSS: type[LossCriticInterface] = MSE_RLLoss

ACTOR_OPTIMIZER: type[torch.optim.Optimizer] = torch.optim.SGD
ACTOR_OPTIMIZER_LR: float = 0.001
ACTOR_OPTIMIZER_MOMENTUM: float = 0.9

CRITIC_OPTIMIZER: type[torch.optim.Optimizer] = torch.optim.SGD
CRITIC_OPTIMIZER_LR: float = 0.001
CRITIC_OPTIMIZER_MOMENTUM: float = 0.9
