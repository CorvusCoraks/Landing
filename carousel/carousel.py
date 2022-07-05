""" Композиция двунаправленной очереди из двух разнонаправленных простых очередей """
from queue import Queue
from typing import Optional, Type, Tuple
# from atrolley import TrolleyType, ATrolley
from copy import deepcopy
from structures import QueueContent, T
from carousel.trolleys import AnyTrolley
from carousel.atrolley import TestId


class Carousel:
    """ Класс инкапсулирует двунаправленную очередь передачи данных в системе. """
    def __init__(self, cargo_prototype: T, trolley_quantity: int):
        """

        :param cargo_prototype: Объект-прототип груза
        :param trolley_quantity: Количество 'вагонеток' в очереди
        """
        # Объект-прототип груза
        self._cargo_prototype: T = cargo_prototype
        # очередь загруженных вагонеток в прямом направлении
        self._queue_loaded: Queue = Queue()
        # очередь пустых вагонеток в обратном направлении
        self._queue_unloaded: Queue = Queue()
        # объект-прототип вагонетки
        self._trolley_prototype: AnyTrolley = AnyTrolley(self._cargo_prototype)
        # количество вагонеток в Carousel
        self._trolley_quantity: int = 0
        # тип груза
        # self.__cargo_class: Type = type(trolley_prototype._cargo)

        for value in range(trolley_quantity):
            self.add_trolley()

    def add_trolley(self) -> None:
        """ Добавить в карусель ещё одну вагонетку """
        self._queue_unloaded.put(deepcopy(self._trolley_prototype))
        self._trolley_quantity += 1

    def del_trolley(self) -> None:
        """ Удалить из карусели одну вагонетку """
        self._queue_unloaded.get()
        self._trolley_quantity -= 1

    @property
    def trolleys_quantity(self) -> int:
        """ Количество вагонеток в карусели """
        return self._trolley_quantity

    def has_new_cargo(self) -> bool:
        """ В очереди имеется полная вагонетка? """
        return not self._queue_loaded.empty()

    def has_void_trolley(self) -> bool:
        """ В очереди имеется пустая вагонетка? """
        return not self._queue_unloaded.empty()

    def unload(self, to_object: T) -> Tuple[TestId, bool]:
        """ Разгрузить вагонетку

        :param to_object: Копировать состояние атрибутов в объект *to_object*
        :return: test_id, is_initial - идентификатор испытания, состояние начальное для нового теста? """
        if type(to_object) is not type(self._cargo_prototype):
            # Если тип целевого объекта не соответствует типу груза в вагонетке
            raise TypeError('Method argument type mismatch: expected {0}, but {1}'.
                            format(type(self._cargo_prototype), type(to_object)))

        trolley: AnyTrolley = self._queue_loaded.get()
        test_id, is_initial = trolley.unload(to_object)
        self._queue_unloaded.put(trolley)
        return test_id, is_initial

    def load(self, test_id: TestId, from_object: T, initial=False) -> None:
        """ Загрузить вагонетку

        :param test_id: Идентификатор теста
        :param from_object: копировать состояние артибутов из объекта *from_object*
        :param initial: это начальное состояние нового испытания?
        """
        if type(from_object) is not type(self._cargo_prototype):
            # Если тип объекта-источника не соответствует типу груза в вагонетке
            raise TypeError('Method argument type mismatch: expected {0}, but {1}'.
                            format(type(self._cargo_prototype), type(from_object)))

        trolley: AnyTrolley = self._queue_unloaded.get()
        trolley.load(test_id, from_object, initial)
        self._queue_loaded.put(trolley)
