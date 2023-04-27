""" Модуль интерфейсов, связанных с хранилищем промежуточных состояний процесса обучения. """
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict


class DictKey(Enum):
    """ Ключи в хранилищах состояний. """
    # Объект этого класса сериализуется в хранилище вместе с данными.

    # Ключи в словаре моделей нейросетей
    ACTOR_MODEL = "actor_model"
    CRITIC_MODEL = "critic_model"

    # Ключи в словаре состояний нейросетей
    ACTOR_STATE = "actor_optim"
    CRITIC_STATE = "critic_optim"

    # Ключи в словаре состояния процесса тренировки
    # OPTIMIZER_STATE = "optimizer_state"
    BATCH_SIZE = "batch_size"
    EPOCH = "epoch_array"               # Начальная эпоха, текущая эпоха, последняя эпоха
    # PREV_Q_MAX = "previous_q_max"
    # DEVICE = "device"
    TEMP_FOR_TEST = "temp_for_test_"

    ACTOR_OPTIMIZER_STATE = 'actor_optimizer_state'
    CRITIC_OPTIMIZER_STATE = 'critic_optimizer_state'


class InterfaceStorage(ABC):
    """ Интерфейс хранилища. Методы хранилища (реализация присуща конкретному хранилищу) для сохранения в нём данных."""
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
        """ Метод хранилища. Хранилище сохраняет в себе данные. """
        ...

    @abstractmethod
    def load(self) -> Dict:
        """ Метод хранилища. Хранилище выгружает из себя данные. """
        ...


class StateInterfaceSaveLoad(ABC):
    """ Интерфейс сохранения и загрузки данных в/из хранилища
    (присущ классу / объекту состояния процесса испытания). """
    @abstractmethod
    def save(self, storage: InterfaceStorage) -> None:
        """ Сохрнить в хранилище.

        :param storage: Хранилище.
        :return: Если True, то прошло успешно.
        """
        # todo Почему возвращаемое значение bool? Где используется? Убрать?
        ...

    @abstractmethod
    def load(self, storage: InterfaceStorage) -> None:
        """ Загрузить из хранилища.

        :param storage: Хранилище.
        :return: Если True, то прошло успешно.
        """
        # todo Почему возвращаемое значение bool? Где используется? Убрать?
        ...


class OptimizerStateInterface(ABC):
    """ Интерфейс доступа к оптимизаторам. """
    @property
    @abstractmethod
    def actor_optim_state(self) -> dict:
        """ Состояние оптимайзера актора. """
        ...

    @actor_optim_state.setter
    @abstractmethod
    def actor_optim_state(self, optim_state: dict) -> None:
        """ Состояние оптимайзера актора. """
        ...

    @property
    @abstractmethod
    def critic_optim_state(self) -> dict:
        """ Состояние оптимайзера критика. """
        ...

    @critic_optim_state.setter
    @abstractmethod
    def critic_optim_state(self, optim_state: dict) -> None:
        """ Состояние оптимайзера критика. """
        ...


class ProcessStateDataInterface(ABC):
    """ Интерфейс доступа к параметрам процесса обучения. """
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

    # @property
    # @abstractmethod
    # def prev_q_max(self) -> float:
    #     ...
    #
    # @prev_q_max.setter
    # @abstractmethod
    # def prev_q_max(self, value) -> None:
    #     ...


class ProcessStateInterface(StateInterfaceSaveLoad, ProcessStateDataInterface, OptimizerStateInterface, ABC):
    """ Состояние процесса обучения. """
    ...
