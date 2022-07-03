""" Абстрактный диспетчер. """
from abc import ABC, abstractmethod
from structures import RealWorldStageStatusN, StageControlCommands
from carousel.metaque import MetaQueueN
from kill_flags import KillCommandsContainer
from typing import Callable, Iterable, Optional, Tuple
from tools import InitialStatusAbstract
from carousel.atrolley import TestId


class DispatcherAbstract(ABC):
    """ Абстрактный класс инкапсулирующий методы работы с источником данных для НС. """
    def __init__(self, batch_size: int,
                 kill: KillCommandsContainer):
        # self._meta_queue = meta_queue
        self._batch_size = batch_size
        # self._tests_max = tests_max
        self._kill = kill
        # self._initial_status_func = initial_status

    @abstractmethod
    def put_zero_state(self, test_id: TestId, initial_state: RealWorldStageStatusN) -> None:
        """ Установить начальное состояние изделия испытании *test_id*. """
        pass

    @abstractmethod
    def run(self, test_id: TestId, command: StageControlCommands) -> Tuple[TestId, RealWorldStageStatusN]:
        """ Метод периодического выхова для обработки команды. """
        pass