""" Конкретный проект (комбинация нейросетей). """
from torch import Tensor, cuda
from torch.nn import Module, Conv2d
import torch.nn.functional as F
from nn_iface.ifaces import ProjectInterface, InterfaceStorage, ProcessStateInterface
from nn_iface.store_nn import ModuleStorage
from nn_iface.store_st import StateStorage, State
from typing import Dict, Optional


class TestModel(Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = Conv2d(1, 20, 5)
        self.conv2 = Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


class AbstractProject(ProjectInterface):
    def __init__(self):
        self._actor_key = "actor"
        self._critic_key = "critic"


class DevelopmentTempProject(AbstractProject):
    def __init__(self):
        super().__init__()
        self.__model_name: str = "first"

        # self.__

        self.__actor: Optional[Module] = None
        self.__critic: Optional[Module] = None

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

        # В хранилище состояния процесса сохраняться не будет.
        self.__device = "cuda:0" if cuda.is_available() else "cpu"

    @property
    def state(self) -> ProcessStateInterface:
        return self.__training_state

    def save_nn(self):
        self.__save_storage_model.save({self._actor_key: self.__actor, self._critic_key: self.__critic})

    def save_state(self):
        self.__training_state.save(self.__save_storage_training_state)

    def load_nn(self):
        try:
            # self.__two_nn.load(self.__load_storage_model)
            actor_and_critic: Dict = self.__load_storage_model.load()
            self.__actor = actor_and_critic[self._actor_key]
            self.__critic = actor_and_critic[self._critic_key]
        except FileNotFoundError:
            # Создание нейросетей.
            self.__actor = TestModel()
            self.__critic = TestModel()

    def load_state(self):
        try:
            # # запоминаем дефолтное значение
            # device_default = self.__training_state.device

            # загружаем состояние из хранилища
            self.__training_state.load(self.__load_storage_training_state)

            # # если в хранилище значение не сохранено.
            # if self.__training_state.device is None:
            #     self.__training_state.device = device_default

            self.__training_state.device = ()
        except FileNotFoundError:
            # Задание начальных состояний для параметров испытаний.
            self.__training_state.batch_size = 1
            self.__training_state.epoch_start = 0
            self.__training_state.epoch_current = 0
            self.__training_state.epoch_stop = 2
            self.__training_state.prev_q_max = 0

    @property
    def device(self) -> str:
        return self.__device

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
