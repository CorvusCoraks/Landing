""" Реализации интерфейсов nn_iface.py """
from typing import Union, Dict, Optional
from torch.nn import Module, Conv2d
import torch.nn.functional as F
from thrds_tk.nn_iface import InterfaceStorage, InterfaceNeuronNet, InterfaceACCombo, ProcessStateInterface


class TestModel(Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = Conv2d(1, 20, 5)
        self.conv2 = Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


class Storage(InterfaceStorage):
    def save(self, suffix: str, i_nn: Optional[InterfaceNeuronNet] = None, data: Optional[Dict] = None) -> None:
        if suffix == "model" and i_nn is not None:
            pass
        elif suffix == "model_state" and i_nn is not None:
            pass
        else:
            pass

    def load(self, suffix: str) -> Union[Module, Dict]:
        if suffix == "model":
            return TestModel()
        elif suffix == "model_state":
            return dict()
        else:
            return dict()


class NeuronNet(InterfaceNeuronNet):
    def create(self) -> None:
        pass

    @property
    def nn(self) -> Module:
        return TestModel()

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
        return TestModel()

    @property
    def critic(self) -> Module:
        return TestModel()

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
        return -1

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        pass
