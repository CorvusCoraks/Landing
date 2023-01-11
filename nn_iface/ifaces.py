""" Интерфейсы модуля нейросети. """
from torch.nn import Module
from torch import Tensor
from abc import ABC, abstractmethod
from typing import Dict
from enum import Enum


class DictKey(Enum):
    # Ключи в словаре моделей нейросетей
    ACTOR_MODEL = "actor_model"
    CRITIC_MODEL = "critic_model"
    # Ключи в словаре состояний нейросетей
    ACTOR_STATE = "actor_state"
    CRITIC_STATE = "critic_state"
    # Ключи в словаре состояния процесса тренировки
    OPTIMIZER_STATE = "optimizer_state"
    BATCH_SIZE = "batch_size"
    EPOCH = "epoch_array"               # Начальная эпоха, текущая эпоха, последняя эпоха
    PREV_Q_MAX = "previous_q_max"
    TEMP_FOR_TEST = "temp_for_test"


class InterfaceNeuronNet(ABC):
    """ Интерфейс одиночной нейросети. """
    @abstractmethod
    def create(self) -> None:
        """ Создать нейросеть. """
        ...

    @property
    @abstractmethod
    def nn(self) -> Module:
        """

        :return: Нейросеть
        """
        ...

    @nn.setter
    @abstractmethod
    def nn(self, value: Module) -> None:
        """

        :param value: Нейросеть.
        """
        ...

    @abstractmethod
    def prepare_input(self) -> None:
        """ Подготовка входных данных. """
        ...

    @abstractmethod
    def proceccing_output(self) -> None:
        """ Обработка выходных данных. """
        ...

    @abstractmethod
    def forward(self) -> None:
        """ Прямой проход. """
        ...

    @abstractmethod
    def backward(self) -> None:
        """ Обратный проход. """
        ...


class InterfaceStorage(ABC):
    """ Интерфейс хранилища. """
    @abstractmethod
    def __init__(self, name: str):
        """

        :param name: Имя сохранения (используется в качестве имени файла с сохранением, имени записи в БД и т. д.)
        """
        ...

    # 1. Сохранение идёт словарями.
    # 2. Содержимое словаря определяется ключом/описанием
    @abstractmethod
    def save(self, any_dict: Dict):
        ...

    @abstractmethod
    def load(self) -> Dict:
        ...


class InterfaceSaveLoad(ABC):
    """ Интерфейс сохранения и загрузки данных в/из хранилища. """
    @abstractmethod
    def save(self, storage: InterfaceStorage) -> None:
        """ Сохрнить в хранилище.

        :param storage: Хранилище.
        :return: Если True, то прошло успешно.
        """
        ...

    @abstractmethod
    def load(self, storage: InterfaceStorage) -> None:
        """ Загрузить из хранилища.

        :param storage: Хранилище.
        :return: Если True, то прошло успешно.
        """
        ...


class InterfaceACCombo(InterfaceSaveLoad):
    """ Интерфейс работы с актором и с критиком. """

    @property
    @abstractmethod
    def actor(self) -> Module:
        """

        :return: Нейросеть.
        """
        ...

    @actor.setter
    @abstractmethod
    def actor(self, value: Module) -> None:
        """

        :param value: Нейросеть.
        """
        ...

    @property
    @abstractmethod
    def critic(self) -> Module:
        """

        :return: Нейросеть.
        """
        ...

    @critic.setter
    @abstractmethod
    def critic(self, value: Module) -> None:
        """

        :param value: Нейросеть.
        """
        ...

    @abstractmethod
    def save(self, storage: InterfaceStorage) -> None:
        ...

    @abstractmethod
    def load(self, storage: InterfaceStorage) -> None:
        ...


class ProcessStateInterface(InterfaceSaveLoad):
    """ Состояние процесса обучения. """
    @abstractmethod
    def save(self, storage: InterfaceStorage) -> None:
        ...

    @abstractmethod
    def load(self, storage: InterfaceStorage) -> None:
        ...

    @property
    @abstractmethod
    def batch_size(self) -> int:
        """

        :return: Размер батча.
        """
        ...

    @batch_size.setter
    @abstractmethod
    def batch_size(self, value: int) -> None:
        """

        :param value: Размер батча.
        """
        ...

    @property
    @abstractmethod
    def epoch_start(self) -> int:
        ...

    @epoch_start.setter
    @abstractmethod
    def epoch_start(self, value: int) -> None:
        ...

    @property
    @abstractmethod
    def epoch_current(self) -> int:
        ...

    @epoch_current.setter
    @abstractmethod
    def epoch_current(self, value: int) -> None:
        ...

    @property
    @abstractmethod
    def epoch_stop(self) -> int:
        ...

    @epoch_stop.setter
    @abstractmethod
    def epoch_stop(self, value: int) -> None:
        ...

    @property
    @abstractmethod
    def prev_q_max(self) -> float:
        ...

    @prev_q_max.setter
    @abstractmethod
    def prev_q_max(self, value) -> None:
        ...


class ProjectInterface(ABC):
    @abstractmethod
    def save(self):
        ...

    @abstractmethod
    def save_state(self):
        ...

    @abstractmethod
    def load(self):
        ...

    @abstractmethod
    def actor_input_preparation(self):
        ...

    @abstractmethod
    def critic_input_preparation(self):
        ...

    @abstractmethod
    def actor_loss(self) -> Tensor:
        ...

    @abstractmethod
    def critic_loss(self) -> Tensor:
        ...

    @abstractmethod
    def actor_optimizer(self):
        ...

    @abstractmethod
    def critic_optimaizer(self):
        ...

    @abstractmethod
    def actor_forward(self) -> Tensor:
        ...

    @abstractmethod
    def critic_forward(self) -> Tensor:
        ...


if __name__ == "__main__":
    pass
