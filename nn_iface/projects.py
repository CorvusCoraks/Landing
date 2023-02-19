""" Конкретный проект (комбинация нейросетей). """
from torch import Tensor
from torch.nn import Module, Conv2d
import torch.nn.functional as F
from nn_iface.ifaces import ProjectInterface, InterfaceStorage, ProcessStateInterface
from typing import Dict, Optional, List, Tuple, Any
from tools import Reinforcement, Finish
from basics import TestId, PROJECT_TOML_FILENAME
from structures import RealWorldStageStatusN
import tomli
from abc import ABC, abstractmethod


class TestModel(Module):
    """ Фиктивная нейросеть для технического временного использования в процессе разработки реализации. """
    def __init__(self):
        super().__init__()
        self.conv1 = Conv2d(1, 20, 5)
        self.conv2 = Conv2d(20, 20, 5)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        return F.relu(self.conv2(x))


class ReadConfigInterface(ABC):
    """ Интерфейс чтения конфигурации проекта из хранилища (файл, БД, удалённый сервер). """
    @abstractmethod
    def load_config(self) -> Dict:
        """ Загрузить настройки проекта в словарь. """
        ...


class ConfigInterpreterInterface(ABC):
    """ Интерфейс-интерпретатор. Интерпретирует загруженные настройки проекта. """
    @abstractmethod
    def interpret(self, config: Dict) -> Tuple[Dict, Any]:
        """ Преобразовать загруженные настройки из словаря в список. """
        ...


class AbstractProject(ProjectInterface):
    """ Абстрактный класс проекта. Объединяет общие атрибуты и реализации методов. """
    def __init__(self):
        self._actor_key = "actor"
        self._critic_key = "critic"

        self._actor: Optional[Module] = None
        self._critic: Optional[Module] = None

        self._training_state: Optional[ProcessStateInterface] = None

        # Хранилища для модуля НС
        self._load_storage_model: Optional[InterfaceStorage] = None
        self._save_storage_model: Optional[InterfaceStorage] = None
        # Хранилище для состояния процесса обучения.
        self._load_storage_training_state: Optional[InterfaceStorage] = None
        self._save_storage_training_state: Optional[InterfaceStorage] = None
        # Хранилище для состояния НС
        self._load_storage_model_state: Optional[InterfaceStorage] = None
        self._save_storage_model_state: Optional[InterfaceStorage] = None

        self._device: str = "cpu"

        # Подкрепление.
        self._reinforcement: Optional[Reinforcement] = None

        # Класс проверки на выход за пределы тестового полигона
        self._finish: Optional[Finish] = None

    @property
    def state(self) -> ProcessStateInterface:
        return self._training_state

    def save_nn(self) -> None:
        self._save_storage_model.save({self._actor_key: self._actor, self._critic_key: self._critic})

    def save_state(self) -> None:
        self._training_state.save(self._save_storage_training_state)

    def load_nn(self) -> None:
        actor_and_critic: Dict = self._load_storage_model.load()
        self._actor = actor_and_critic[self._actor_key]
        self._critic = actor_and_critic[self._critic_key]

    def load_state(self) -> None:
        # загружаем состояние из хранилища
        self._training_state.load(self._load_storage_training_state)

    @property
    def device(self) -> str:
        return self._device

    @property
    def reinforcement(self) -> Reinforcement:
        return self._reinforcement

    @property
    def finish(self) -> Finish:
        return self._finish

    def critic_input_preparation(self, actor_output: Tensor, environment_batch: Dict[TestId, RealWorldStageStatusN]) -> Tensor:
        pass

    def actor_loss(self) -> Tensor:
        pass

    def critic_loss(self) -> Tensor:
        pass

    def actor_optimizer(self) -> None:
        pass

    def critic_optimaizer(self) -> None:
        pass

    def actor_forward(self, actor_input: Tensor) -> Tensor:
        ### Проверка на совпадение количества входных параметров, размерности feaches нейронной сети.
        #
        # Итератор по слоям актора.
        childrens_iter = self._actor.children()
        # Первый слой - слой входных нейронов.
        first_children = childrens_iter.__next__()
        # Второй слой - линейный слой. По нему считаем количество и входных нейронов.
        second_children = childrens_iter.__next__()
        # Итератор по параметрам второго, линейного слоя.
        second_children_parameters_iter = second_children.parameters(recurse=True)
        # Параметры второго, линейного слоя.
        second_children_parameters = second_children_parameters_iter.__next__()
        # Число входных параметров должно соответствовать числу входных нейронов.
        # shape по тензору: [число подтензоров (элементов батча), количество feaches в элементе батча]
        # shape по параметрам: [число нейронов скрытого слоя, число входных нейронов]
        assert second_children_parameters.shape[1] == actor_input.shape[1], \
            "Width of raw_batch element ({}) mismatch of neuron net input feaches count ({})." \
            "May be you change neuron net input width in project, but load old neuron net from storage?".\
                format(second_children_parameters[1], actor_input.shape[1])
        #
        ### Конец проверки.

        return self._actor.forward(actor_input)
        # return actor_input

    def critic_forward(self, critic_input: Tensor) -> Tensor:
        pass
