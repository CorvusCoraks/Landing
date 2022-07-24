""" Реализации конкретных 'вагонеток' для каруселей из реальных данных. """
from carousel.atrolley import ATrolley, TestId
from structures import RealWorldStageStatusN, StageControlCommands, T, ValueCopyInterface
from typing import TypeVar, Tuple, Optional, Type, Callable, Any




class AnyTrolley(ATrolley):
    def __init__(self, cargo_default: T):
        # QueueContent.__init__(self)
        ATrolley.__init__(self)
        # self._cargo_type = cargo_type
        self._cargo = cargo_default

    def unload(self, to_object: T) -> Tuple[TestId, bool]:
        self._cargo.data_copy(to_object)
        self._is_loaded = False
        return self._test_id, self._is_initial

    def load(self, test_id: TestId, from_object: T, initial=False) -> None:
        # ATrolley.load(self, test_id, from_object)
        self._test_id = test_id
        self.is_initial = initial
        from_object.data_copy(self._cargo)
        self._is_loaded = True


# class FreeTrolley(ATrolley):
#     # Значения атрибутов объекта лежат в чемодан.
#     # Чемодан лежит в вагонетке
#     #
#     # Загрузка вагонетки делается следующим порядком:
#     # - загрузка чемодана определённого типа в вагонетку из буфера чемоданов карусели
#     # - загрузка груза в чемодан определённого типа
#     # Разгрузка вагонетки делается следующим порядком:
#     # - считывание типа чемодана (типа груза)
#     # - выгрузка груза (копированием значений атрибутов) во внешний объект определённого типа.
#     # - выгрузка чемодана из вагонетки
#     #
#     # Чемодан, это - пустой объект определённого типа, служащий временным вместилищем (на время транспортировки)
#     # значений атрибутов
#     #
#     # Чемоданы постоянно хранятся в соответствующей карусели
#     # и по мере необходимости связываются перед загрузкой с вагонетками и отсоединяются от них после разгрузки.
#     #
#     # Таким образом, каждая вагонетка приспособлена для перевозки грузов любых типов, лишь бы был свободный чемодан.
#     def __init__(self):
#         ATrolley.__init__(self)
#         # self.__cargo_type: Optional[Type] = None
#         self._cargo: Optional[ValueCopyInterface] = None
#
#     def chest_load(self, chest: ValueCopyInterface):
#         self._cargo = chest
#
#     def chest_unload(self):
#         self._cargo = None
#
#     @property
#     def cargo_type(self) -> Optional[Type]:
#         return type(self._cargo) if self._cargo != None else None
#
#     def unload(self, to_object: ValueCopyInterface) -> Tuple[TestId, bool]:
#         self._cargo.data_copy(to_object)
#         self._is_loaded = False
#         return self._test_id, self._is_initial
#
#     def load(self, test_id: TestId, from_object: ValueCopyInterface, initial: bool) -> None:
#         self._test_id = test_id
#         self.is_initial = initial
#         from_object.data_copy(self._cargo)
#         self._is_loaded = True

# class RealWorldTrolleyN(AnyTrolley):
#     def __init__(self, cargo_default: RealWorldStageStatusN):
#         AnyTrolley.__init__(self, cargo_default)
#
#
# class CommandTrolleyN(AnyTrolley):
#     def __init__(self, cargo_default: StageControlCommands):
#         AnyTrolley.__init__(self, cargo_default)

# if __name__ == '__main__':
#     rw_trolley = RealWorldTrolleyN(RealWorldStageStatusN(time_stamp=0))


# class RealWorldTrolley(ATrolley, RealWorldStageStatusN):
#     """ 'Вагонетка' с объектом состояния в реальном мире. """
#     def __init__(self):
#         RealWorldStageStatusN.__init__(self)
#         ATrolley.__init__(self)
#
#     def unload(self, to_object: RealWorldStageStatusN):
#         self.data_copy(to_object)
#         self._is_loaded = False
#
#     def load(self, test_id: int, from_object: RealWorldStageStatusN):
#         # ATrolley.load(self, test_id, from_object)
#         self._test_id = test_id
#         from_object.data_copy(self)
#         self._is_loaded = True
#
#
# class CommandTrolley(ATrolley, StageControlCommands):
#     def __init__(self):
#         StageControlCommands.__init__(self, -1)
#         Trolley.__init__(self)

    # def unload(self, to_object: StageControlCommands):
    #     self.data_copy(to_object)
    #     self._is_loaded = False
    #
    # def load(self, test_id: int, from_object: StageControlCommands):
    #     # ATrolley.load(self, test_id, from_object)
    #     self._test_id = test_id
    #     from_object.data_copy(self)
    #     self._is_loaded = True

class TrolleyA():
    """ Класс 'вагонетки', которая циркулирует по одиночной карусели сообщений. """
    def __init__(self):
        self._is_loaded: bool = False   # Вагонетка загружена?
        # Контейнер с неизвестным объектом
        self._cargo_unknown: Any = None
    #     self._cargo_type: Optional[QueueContent] = None
    #
    # @property
    # def cargo_type(self) -> QueueContent:
    #     return self._cargo_type
    #
    # @cargo_type.setter
    # def cargo_type(self, value: QueueContent) -> None:
    #     self._cargo_type = value

    @property
    def is_loaded(self) -> bool:
        """ Вагонетка загружена? """
        return self._is_loaded

    @is_loaded.setter
    def is_loaded(self, value: bool) -> None:
        """ Вагонетка загружена? """
        self._is_loaded = value

    def loading(self, cargo_unknown: Any) -> None:
        """ Загрузка вагонетки (погрузка контейнера) """
        self._cargo_unknown = cargo_unknown
        self._is_loaded = True

    def unloading(self) -> Any:
        """ Разгрузка вагонетки (выгрузка контейнера)"""
        self._is_loaded = False
        return self._cargo_unknown
