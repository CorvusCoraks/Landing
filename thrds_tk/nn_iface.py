from torch.nn import Module
from abc import ABC, abstractmethod
from typing import Dict, Optional, Union, overload
from torch import nn


class InterfaceNeuronNet(ABC):
    """ Интерфейс одиночной нейросети. """
    @abstractmethod
    def create(self) -> None:
        """ Создать нейросеть. """
        ...

    @abstractmethod
    @property
    def nn(self) -> Module:
        """

        :return: Нейросеть
        """
        ...

    @abstractmethod
    @nn.setter
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
    # def __init__(self, name: str):
    #     """
    #
    #     :param name: Имя сохранения (используется в качестве имени файла с сохранением, имени записи в БД и т. д.)
    #     """
    #     ...

    @overload
    @abstractmethod
    def save(self, i_nn: InterfaceNeuronNet, suffix="model") -> None:
        """ Сохранить модель модель нейросети и её гиперпараметры.

        :param i_nn: Нейросеть для сохранения.
        :param suffix: Имя подраздела в хранилище.
        """
        ...

    @overload
    @abstractmethod
    def save(self, i_nn: InterfaceNeuronNet, suffix="model_state") -> None:
        """ Сохранить гиперпараметры нейросети.

        :param i_nn: Нейросеть для сохранения.
        :param suffix: Имя подраздела в хранилище.
        """
        ...

    @overload
    @abstractmethod
    def save(self, data: Dict, suffix: str) -> None:
        """ Сохранить иные данные.

        :param data: Любые данные в виде словаря для сохранения.
        :param suffix: Имя подраздела в хранилище.
        """
        ...

    @abstractmethod
    def save(self, suffix: str, i_nn: Optional[InterfaceNeuronNet] = None, data: Optional[Dict] = None) -> None:
        """

        :param suffix: Имя подраздела в хранилище
        :param i_nn: Нейросеть для сохранения.
        :param data: Любые данные в виде словаря для сохранения.
        """
        # if suffix == "model" and i_nn is not None:
        #     ...
        # elif suffix == "model_state" and i_nn is not None:
        #     ...
        # else:
        #     ...
        ...

    @abstractmethod
    def load(self, suffix: str) -> Union[nn.Module, Dict]:
        """ Восстановить ранее сохранённые данные.

        :param suffix: suffix="model|model_state|any_other_states"
        :return: Или нейросеть, или словарь с некими параметрами.
        """
        # if suffix == "model":
        #     pass
        #     return nn.Module()
        # elif suffix == "model_state":
        #     pass
        #     return dict()
        # else:
        #     ...
        ...


class InterfaceSaveLoad(ABC):
    """ Интерфейс сохранения и загрузки данных в/из хранилища. """
    @abstractmethod
    def save(self, storage: InterfaceStorage) -> bool:
        """ Сохрнить в хранилище.

        :param storage: Хранилище.
        :return: Если True, то прошло успешно.
        """
        ...

    @abstractmethod
    def load(self, storage: InterfaceStorage) -> bool:
        """ Загрузить из хранилища.

        :param storage: Хранилище.
        :return: Если True, то прошло успешно.
        """
        ...


class InterfaceACCombo(InterfaceSaveLoad):
    """ Интерфейс работы с актором и с критиком. """
    @abstractmethod
    @property
    def actor(self) -> Module:
        """

        :return: Нейросеть.
        """
        ...

    @abstractmethod
    @actor.setter
    def actor(self, value: Module) -> None:
        """

        :param value: Нейросеть.
        """
        ...

    @abstractmethod
    @property
    def critic(self) -> Module:
        """

        :return: Нейросеть.
        """
        ...

    @abstractmethod
    @critic.setter
    def critic(self, value: Module) -> None:
        """

        :param value: Нейросеть.
        """
        ...

    @abstractmethod
    def save(self, storage: InterfaceStorage) -> bool:
        ...

    @abstractmethod
    def load(self, storage: InterfaceStorage) -> bool:
        ...


class ProcessStateInterface(InterfaceSaveLoad):
    """ Состояние процесса обучения. """
    @abstractmethod
    def save(self, storage: InterfaceStorage) -> bool:
        ...

    @abstractmethod
    def load(self, storage: InterfaceStorage) -> bool:
        ...

    @abstractmethod
    @property
    def batch_size(self) -> int:
        """

        :return: Размер батча.
        """
        ...

    @abstractmethod
    @batch_size.setter
    def batch_size(self, value: int) -> None:
        """

        :param value: Размер батча.
        """
        ...
