""" Реализация хранилища нейросетей. """
from torch.nn import Module, Conv2d
import torch.nn.functional as F
from nn_iface.ifaces import InterfaceNeuronNet
from fl_store.pt_store import TorchFileStorage


# todo здесь этому классу не место. Удалить.
class TestModel(Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = Conv2d(1, 20, 5)
        self.conv2 = Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


class ModuleStorage(TorchFileStorage):
    """ Хранилище структуры нейросетей (и актора, и критика). """
    # def __init__(self, research_name: str):
    #     super().__init__(research_name)
    def __init__(self, file_name: str):
        super().__init__(file_name)
        # self._storage_filename = self._storage_filename.format("_nn")
        self._storage_filename = file_name


# todo Класс не используется. Удалить?
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

