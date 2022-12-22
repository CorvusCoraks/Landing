""" Реализации интерфейсов nn_iface.py """
from abc import abstractmethod
from typing import Union, Dict, Optional, overload

from torch import nn
from torch.nn import Module

from thrds_tk.nn_iface import InterfaceStorage, InterfaceNeuronNet, InterfaceACCombo, ProcessStateInterface


class Storage(InterfaceStorage):
    def save(self, suffix: str, i_nn: Optional[InterfaceNeuronNet] = None, data: Optional[Dict] = None) -> None:
        pass

    def load(self, suffix: str) -> Union[nn.Module, Dict]:
        pass


class NeuronNet(InterfaceNeuronNet):
    def create(self) -> None:
        pass

    @property
    def nn(self) -> Module:
        pass

    def prepare_input(self) -> None:
        pass

    def proceccing_output(self) -> None:
        pass

    def forward(self) -> None:
        pass

    def backward(self) -> None:
        pass


class ActorAndCritic(InterfaceACCombo):
    @property
    def actor(self) -> Module:
        pass

    @property
    def critic(self) -> Module:
        pass

    def save(self, storage: InterfaceStorage) -> bool:
        pass

    def load(self, storage: InterfaceStorage) -> bool:
        pass


class State(ProcessStateInterface):
    def save(self, storage: InterfaceStorage) -> bool:
        pass

    def load(self, storage: InterfaceStorage) -> bool:
        pass

    @property
    def batch_size(self) -> int:
        return 0

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        pass