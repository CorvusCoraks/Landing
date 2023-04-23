""" Интерфейсы модуля нейросети. """
from torch.nn import Module
from torch import Tensor
import torch.optim
from abc import ABC, abstractmethod
from typing import Dict, List
from nn_iface.if_state import ProcessStateInterface
from tools import Reinforcement, Finish
from basics import TestId
from structures import RealWorldStageStatusN
from basics import ZeroOne


class LossCriticInterface(ABC):
    """ Интерфейс класса функции потерь. """
    @abstractmethod
    def __call__(self, s_order: List[TestId], reinf: Dict[TestId, ZeroOne],
                 max_q_est: Dict[TestId, ZeroOne], max_q_est_next: Tensor) -> Tensor:
        ...


class LossActorInterface(ABC):
    """ Интерфейс класса функции потерь актора. """
    @abstractmethod
    def __call__(self, output: Tensor, target: Tensor) -> Tensor:
        ...


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


class ProjectInterface(ABC):
    """ Интерфейс тестируемого варианта системы актор-критик. """
    # Взаимодействие потока обучения должно происходить исключительно с этим интерфейсом,
    # но не непосредственно с нейросетями.
    @property
    @abstractmethod
    def state(self) -> ProcessStateInterface:
        """ Состояние процесса тренировки. """
        ...

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
        """ Объект подкрепления. """
        ...

    @property
    @abstractmethod
    def finish(self) -> Finish:
        """ Объект окончания конкретного испытания. """
        ...

    @abstractmethod
    def actor_input_preparation(self, batch: Dict[TestId, RealWorldStageStatusN], s_order: List[TestId]) \
            -> Tensor:
        """ Подготовка входных данных для актора.

        :param batch: Запланированный для прохода через актора батч.
        :param s_order: список, содержащий порядок испытаний во входном тензоре актора.
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
        :param s_order: список, содержащий порядок испытаний во входном тензоре актора.
        :return: Входной батч критика в виде тензора.
        """
        ...

    @abstractmethod
    def critic_output_transformation(self, all_q_est: Tensor, s_order: List[TestId],
                                     max_q_est_index: Dict[TestId, int]) -> Tensor:
        """ Преобразование выходного тензора критика,
        содержащего ВСЕ оценки ф-ции ценности по ВСЕМ вариантам действий ВСЕХ испытаний в батче,
        в тензор, содержащий только макс. оценки ф-ции ценности по каждому испытанию в батче.

        :param all_q_est: выход критика
        :param s_order: Список идентификаторов тестов, соответсвующих порядку тестов в тензоре входа актора
        :param max_q_est_index: Словарь,
        содержащий индексы максимальных оценок функции ценности для каждого испытания в батче.
        """
        ...

    @property
    @abstractmethod
    def actor_loss(self) -> LossActorInterface:
        """ Функция потерь актора. """
        ...

    @property
    @abstractmethod
    def critic_loss(self) -> LossCriticInterface:
        """ Функция потерь критика. """
        ...

    @property
    @abstractmethod
    def actor_optimizer(self) -> torch.optim.Optimizer:
        """ Оптимайзер актора. """
        ...

    @property
    @abstractmethod
    def critic_optimizer(self) -> torch.optim.Optimizer:
        """ Оптимайзер критика. """
        ...

    @abstractmethod
    def actor_forward(self, actor_input: Tensor) -> Tensor:
        """ Прямой проход актора. """
        ...

    @abstractmethod
    def critic_forward(self, critic_input: Tensor) -> Tensor:
        """ Прямой проход критика. """
        ...

    @abstractmethod
    def max_in_q_est(self, q_est_next: Tensor, s_order: List[TestId]) -> Dict[TestId, int]:
        """ Метод выбора максимального значения оценки функции ценности.

        :param q_est_next: Тензор оценок функции ценности для всех возможных действий актора (ВЫХОД критика)
        :param s_order: Список идентификаторов тестов, соответсвующих порядку тестов в тензоре входа актора
        :return: Словарь индексов максимальных значений оценки функции ценности (индекс соответствует индексу действия)
        """

        ...

    @abstractmethod
    def choose_max_q_action(self, s_order: List[TestId], max_q_index: Dict[TestId, int]) -> \
            Dict[TestId, Tensor]:
        """ Выбор действия актора (для каждого испытания в батче), отвечающего максимальной оценке функции ценности.

        :param s_order: Список идентификаторов тестов, соответсвующих порядку тестов в тензоре входа актора
        :param max_q_index: Словарь, содержащий индексы максимальных оценок функции ценности
        для КАЖДОГО испытания в батче. Каждое испытание в батче имеет несколько оценок функции ценности
        (по числу возможных действий актора). Одна запись словаря содержит индекс максимальной оценки
        в массиве этих вариантов.
        :return: Словарь вида: идентификатор испытания - тензор действия актора.
        """
        ...

    @abstractmethod
    def actor_target(self, s_order: List[TestId], commands: Dict[TestId, Tensor]) -> Tensor:
        """ Целевой выход актора (зависит от распределения максимальных оценок функции ценности по батчу).

        :param s_order: Список идентификаторов тестов, соответсвующих порядку тестов в тензоре входа актора
        :param commands: Словарь команд (желаемых действий актора), как следствие выбранных максимальных оценок ФЦ.
        :return: Тензор целевого выхода актора.
        """
        ...


if __name__ == "__main__":
    pass
