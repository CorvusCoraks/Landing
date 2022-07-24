""" Абстракции двунаправленной очереди. """
from abc import ABC, abstractmethod
from typing import Tuple, Optional,Type, Any, TypeVar
from structures import ValueCopyInterface, RealWorldStageStatusN, T, TestId


# Тип вагонетки: ВСЕ дочерние подтипы от ATrolley.
# TrolleyType = TypeVar('TrolleyType', bound='ATrolley')
# TestId = int

M = TypeVar('M', int, bool)
# class ILoadUnload


class ATrolley(ABC):
    """ Абстрактный класс описывающий 'вагонетку', которая циркулирует по карусели сообщений. """
    def __init__(self):
        self._is_loaded: bool = False   # Вагонетка загружена?
        self._test_id: TestId = -1
        self._is_initial = False

    @abstractmethod
    def unload(self, to_object: ValueCopyInterface) -> Tuple[TestId, bool]:
        """ Метод разгрузки вагонетки во внешний объект *to_object*

        :return: test_id, is_initial
        """
        pass

    @abstractmethod
    def load(self, test_id: TestId, from_object: ValueCopyInterface, initial: bool) -> None:
        """ Загрузить вагонетку грузом с идентификатором *test_id* из объекта *from_object* """
        # temp = from_object.data_copy()
        pass

    @property
    def is_loaded(self) -> bool:
        """ Вагонетка загружена? """
        return self._is_loaded

    @is_loaded.setter
    def is_loaded(self, value: bool) -> None:
        """ Вагонетка загружена? """
        self._is_loaded = value

    # @abstractmethod
    # def _set_default(self):
    #     pass

    @property
    def test_id(self) -> TestId:
        """ Получить идентификатор конкретного испытания. """
        return self._test_id

    @test_id.setter
    def test_id(self, value: TestId) -> None:
        """ Установить идентификатор конкретного испытания. """
        self._test_id = value

    @property
    def is_initial(self) -> bool:
        """ В вагонетке начальное положение? """
        return  self._is_initial

    @is_initial.setter
    def is_initial(self, value: bool):
        """ В вагонетке начальное положение? """
        self._is_initial = value


class TrolleyAbstract(ABC):
    """ Абстрактный класс описывающий 'вагонетку', которая циркулирует по карусели сообщений. """
    # todo Проверить на используемость и убрать при необходимости.
    def __init__(self):
        self._is_loaded: bool = False   # Вагонетка загружена?
        # self._cargo: Optional[Any] = None
        # self._cargo_type: Optional[Type] = None
        # self._unloaded_object: Optional[Any] = None

    # @property
    # def load_method(self):
    #     """
    #
    #     :return: метод разгрузки вагонетки
    #     """
    #     if type(self._cargo) == ValueCopyInterface:
    #         return ValueCopyInterface
    #     else:
    #         return None

    @property
    def is_loaded(self) -> bool:
        """ Вагонетка загружена? """
        return self._is_loaded

    @is_loaded.setter
    def is_loaded(self, value: bool) -> None:
        """ Вагонетка загружена? """
        self._is_loaded = value

    @abstractmethod
    def loading(self, *args) -> Optional[Tuple]:
        pass

    @abstractmethod
    def unloading(self, *args) -> Optional[Tuple]:
        """ Разгрузка вагонетки """
        pass
