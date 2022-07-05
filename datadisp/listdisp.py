""" Диспетчер, реализующий множество псевдо-параллельных испытаний в виде списка. """
from datadisp.adisp import DispatcherAbstract
from carousel.metaque import MetaQueueN
from structures import RealWorldStageStatusN, StageControlCommands
from kill_flags import KillCommandsContainer
from time import sleep
from tools import InitialStatusAbstract
from typing import Optional, Tuple
from carousel.atrolley import TestId
from physics import Moving


class Element:
    """ Элемент коллекции текущих испытаний. """
    def __init__(self):
        self.__test_id: TestId = -1
        self.__value: Optional[RealWorldStageStatusN] = None

    @property
    def test_id(self) -> TestId:
        return self.__test_id

    @test_id.setter
    def test_id(self, value: TestId):
        self.__test_id = value

    @property
    def state(self) -> RealWorldStageStatusN:
        return self.__value

    @state.setter
    def state(self, value: RealWorldStageStatusN):
        self.__value = value


class ListDispatcher(DispatcherAbstract):
    """ Класс реализует множество параллельно-последовательных расчётов состояний. """

    def __init__(self, batch_size: int, kill: KillCommandsContainer):
        DispatcherAbstract.__init__(self, batch_size, kill)
        # хранилище состояний испытаний.
        # Номер испытания (test_id) совпадает с индексом испытания в кортеже испытаний.
        self.__tests_list: tuple = tuple([Element() for i in range(batch_size)])

    def put_zero_state(self, test_id: TestId, initial_state: Optional[RealWorldStageStatusN]):
        """ Установить в хранилище состояний начальное состояние *initial_state* испытания *test_id*

        :param initial_state: Если равен *None*, значит начальные состояния закончились. """

        self.__tests_list[test_id].state = initial_state
        self.__tests_list[test_id].test_id = test_id

    def run(self, test_id: TestId, command: StageControlCommands, new_state: RealWorldStageStatusN) -> TestId:
        """ Расчёт нового состояния для одного испытания.

        :return: Идентификатор состояния/испытания"""
        # tate: RealWorldStageStatusN

        previous_state = self.__tests_list[test_id].state

        Moving.get_new_status(command, previous_state, new_state)

        self.__tests_list[test_id].state = new_state

        return test_id