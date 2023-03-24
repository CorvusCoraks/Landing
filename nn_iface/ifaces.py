""" Интерфейсы модуля нейросети. """
from torch.nn import Module
from torch import Tensor
from torch import device as torch_device
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, List
from enum import Enum
from tools import Reinforcement, Finish
from basics import TestId
from structures import RealWorldStageStatusN


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
    # DEVICE = "device"
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

    # @property
    # @abstractmethod
    # def device(self) -> Optional[str]:
    #     ...
    #
    # @device.setter
    # @abstractmethod
    # def device(self, value: str) -> None:
    #     ...

class ProjectInterface(ABC):
    """ Интерфейс тестируемого варианта системы актор-критик. """
    # Взаимодействие потока обучения должно происходить исключительно с этим интерфейсом,
    # но не непосредственно с нейросетями.
    @property
    @abstractmethod
    def state(self) -> ProcessStateInterface:
        """ Состояние процесса тренировки. """
        ...

    # @state.setter
    # @abstractmethod
    # def state(self):
    #     ...

    @abstractmethod
    def save_nn(self) -> None:
        """ Сохранить модель нейросети. """
        ...

    @abstractmethod
    def save_state(self) -> None:
        """ Сохранить состояние нейросети и состояние процесса тренировки. """
        ...

    @abstractmethod
    def load_nn(self) -> None:
        """ Загрузить модель нейросети. """
        ...

    @abstractmethod
    def load_state(self) -> None:
        """ Загрузить состояние нейросети и состояние процесса тренировки. """
        ...

    @property
    @abstractmethod
    def device(self) -> str:
        """ Устройство для обсчёта тензоров. Пример: 'cuda:0','cpu' """
        ...

    @property
    @abstractmethod
    def reinforcement(self) -> Reinforcement:
        ...

    @property
    @abstractmethod
    def finish(self) -> Finish:
        ...

    @abstractmethod
    def actor_input_preparation(self, batch: Dict[TestId, RealWorldStageStatusN], s_order: List[TestId]) \
            -> Tensor:
        """ Подготовка входных данных для актора.

        :param batch: Запланированный для прохода через актора батч.
        :return: Входной батч актора в виде тензора и список с идентификаторами испытаний.
        """
        ...

    @abstractmethod
    def critic_input_preparation(self, actor_input: Tensor, actor_output: Tensor,
                                 environment_batch: Dict[TestId, RealWorldStageStatusN], s_order: List[TestId]) \
            -> Tensor:
        """ Подготовка входных данных для критика.

        :param actor_input: Вход в актора.
        :param actor_output: Выход из актора.
        :param environment_batch: Проведённый через актора батч исходных данных.
        :param s_order: список, содержащий порядок испытаний во входрном тензоре актора.
        :return: Входной батч критика в виде тензора.
        """
        ...

    @abstractmethod
    def actor_loss(self) -> Tensor:
        """ Функция потерь актора. """
        ...

    @abstractmethod
    def critic_loss(self) -> Tensor:
        """ Функция потерь критика. """
        ...

    @abstractmethod
    def actor_optimizer(self) -> None:
        """ Оптимизатор актора ? """
        ...

    @abstractmethod
    def critic_optimaizer(self) -> None:
        """ Оптимизатор критика ? """
        ...

    @abstractmethod
    def actor_forward(self, actor_input: Tensor) -> Tensor:
        """ Прямой проход актора. """
        ...

    @abstractmethod
    def critic_forward(self, critic_input: Tensor) -> Tensor:
        """ Прямой проход критика. """
        ...


if __name__ == "__main__":
    pass
