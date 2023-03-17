""" Настройки проекта. """
from torch.nn import Sequential, Sigmoid, Linear
from typing import List, Dict, Any

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
