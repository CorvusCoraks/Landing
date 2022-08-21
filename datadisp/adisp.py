""" Абстрактный диспетчер. """
from abc import ABC, abstractmethod
from structures import RealWorldStageStatusN, StageControlCommands
from carousel.metaque import MetaQueueN
from kill_flags import KillCommandsContainerN
from typing import Callable, Iterable, Optional, Tuple
from tools import InitialStatusAbstract
from carousel.atrolley import TestId


class DispatcherAbstract(ABC):
    """ Абстрактный класс инкапсулирующий методы работы с источником данных для НС. """
    def __init__(self, batch_size: int,
                 kill: KillCommandsContainerN):
        """

        :param batch_size: Размер батча в нейросети.
        :param kill: Блок флагов на завершение нитей.
        """
        # self._meta_queue = meta_queue
        self._batch_size = batch_size
        # self._tests_max = tests_max
        self._kill = kill
        # self._initial_status_func = initial_status

    @abstractmethod
    def is_all_tests_ended(self) -> bool:
        """ Все запланированные испытания завершены?

        :return: все запланированные испытания завершены?
        """
        pass

    @abstractmethod
    def put_zero_state(self, test_id: TestId, initial_state: RealWorldStageStatusN) -> None:
        """ Установить начальное состояние изделия испытании *test_id*.

        :param test_id: Идентификатор испытания.
        :param initial_state: Начальные параметры изделия для данного испытания.
        Если = None, то значит, что пул начальных состояний пуст.
        """
        pass

    @abstractmethod
    def run(self, test_id: TestId, command: StageControlCommands, state: RealWorldStageStatusN) -> TestId:
        """ Расчёт нового состояния для одного испытания.

        :param test_id: Идентификатор испытания.
        :param command: Команда управления.
        :param state: Новое состояние после применения команды управления.
        :return: Идентификатор испытания
         """
        pass