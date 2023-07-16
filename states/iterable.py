""" Классы инициализации начальных состояний через итерируемые объекты. """
from abc import ABC, abstractmethod
from math import pi
from typing import Iterable, Tuple, Optional
from app_type import TestId
from point import VectorComplex
from stage import BigMap
from structures import RealWorldStageStatusN

# InitialStatusAbstract (iterable interface)  -> InitialStatus (iterable realization)
#           └> another iterable realization

class InitialStatusAbstract(ABC, Iterable):
    """ Итерируемый объект начальных состояний изделия.
    Когда начальные состояния изделия в объекте иссякают, он должен возвращать *None*"""
    def __init__(self, max_count):
        """

        :param max_count: максимальное количество начальных состояний (запланированных испытаний).
        """
        self._current_status_index: int = -1
        self._max_status_index: int = max_count - 1
        self._is_empty: bool = False

    @abstractmethod
    def __iter__(self):
        pass

    # def iter(self):

    @abstractmethod
    def __next__(self) -> Tuple[Optional[TestId], Optional[RealWorldStageStatusN]]:
        """ Когда итерируемый объект опустошается, данный метод должен возвращать *None*"""
        pass

    @property
    def is_empty(self) -> bool:
        """ Итерируемый объект пуст?

        :return: Итерируемый объект пуст?
        """
        return self._is_empty

    @abstractmethod
    def remaining_count(self) -> int:
        ...


class InitialStatus(InitialStatusAbstract):
    def __init__(self, max_count: int):
        InitialStatusAbstract.__init__(self, max_count)

    def __iter__(self):
        self._current_status_index = -1
        self._is_empty = False
        return self

    def __next__(self) -> Tuple[Optional[TestId], Optional[RealWorldStageStatusN]]:
        self._current_status_index += 1
        if self._is_empty:
            # Когда закончились начальные состояния, метод начинает возвращать *None*
            self._current_status_index -= 1
            return None, None
        else:
            if self._current_status_index == self._max_status_index:
                # Последний элемент, последовательность пуста.
                self._is_empty = True

            assert isinstance(self._current_status_index, TestId), "Iterator index 'int'-type couldn't cast to TestId " \
                                                                   "class: TestId is not a subclass of 'int'-type."
            return self._current_status_index, RealWorldStageStatusN(position=VectorComplex.get_instance(0., BigMap.startPointInPoligonCoordinates.y - self._current_status_index),
                                     orientation=VectorComplex.get_instance(0., 1.),
                                     velocity=VectorComplex.get_instance(0., -5.),
                                     angular_velocity=-pi/36)

    def remaining_count(self) -> int:
        return self._max_status_index - self._current_status_index
