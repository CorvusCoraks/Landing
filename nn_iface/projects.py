""" Конкретный проект (комбинация нейросетей). """
from torch import Tensor
from torch.nn import Module, Conv2d
import torch.nn.functional as F
from ifaces import ProjectInterface, InterfaceStorage, ProcessStateInterface
from store_nn import ModuleStorage
from store_st import StateStorage, State


class TestModel(Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = Conv2d(1, 20, 5)
        self.conv2 = Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


class DevelopmentTempProject(ProjectInterface):
    def __init__(self):
        self.__model_name: str = "first"

        self.__actor: Module = TestModel()
        self.__critic: Module = TestModel()

        # Хранилища для модуля НС
        self.__load_storage_model: InterfaceStorage = ModuleStorage(self.__model_name)
        self.__save_storage_model: InterfaceStorage = self.__load_storage_model
        # Хранилище для состояния процесса обучения.
        self.__load_storage_training_state: InterfaceStorage = StateStorage(self.__model_name)
        self.__save_storage_training_state: InterfaceStorage = self.__load_storage_training_state
        # Хранилище для состояния НС
        self.__load_storage_model_state: InterfaceStorage = self.__load_storage_training_state
        self.__save_storage_model_state: InterfaceStorage = self.__load_storage_training_state

        self.__training_state: ProcessStateInterface = State()

    def save(self):
        pass
        # self.__two_nn.save(self.__save_storage_model_state)

    def save_state(self):
        self.__training_state.save(self.__save_storage_training_state)

    def load(self):
        # try:
        #     self.__two_nn.load(self.__load_storage_model)
        # except FileNotFoundError:
        #     # Создание нейросетей.
        #     pass

        try:
            self.__training_state.load(self.__load_storage_training_state)
        except FileNotFoundError:
            # Задание начальных состояний для параметров испытаний.
            self.__training_state.batch_size = 1
            self.__training_state.epoch_start = 0
            self.__training_state.epoch_current = 0
            self.__training_state.epoch_stop = 2
            self.__training_state.prev_q_max = 0

    def actor_input_preparation(self):
        pass

    def critic_input_preparation(self):
        pass

    def actor_loss(self) -> Tensor:
        pass

    def critic_loss(self) -> Tensor:
        pass

    def actor_optimizer(self):
        pass

    def critic_optimaizer(self):
        pass

    def actor_forward(self) -> Tensor:
        pass

    def critic_forward(self) -> Tensor:
        pass

