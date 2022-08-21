from point import VectorComplex
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Union, Any, TypeVar, Optional, Type, Tuple, Dict, overload


# QueueContent = Union['StageControlCommands', 'RealWorldStageStatusN', 'ReinforcementValue']
T = TypeVar('T', 'RealWorldStageStatusN', 'StageControlCommands', 'ReinforcementValue', 'MessageBase')
# Идентификатор конкретного испытания.
TestId: Type[int] = int
# Класс отметки времени конкретного испытания.
TimeStamp: Type[int] = int
# BlockType = TypeVar('BlockType', bound='QueueBlock')
# link_containers_and_data = 'DataAndContainers'.get_instanse()

class CloneInterface(ABC):
    # todo Возможно - избыточный интерфейс
    @abstractmethod
    def clone(self):
        """ Клонирование объекта (реализация паттерна Прототип). """
        pass


class ValueCopyInterface(ABC):
    @abstractmethod
    def data_copy(self, target_object: Any):
        """ Копирование значений атрибутов объекта в другой объект такого же типа
        (без создания объектов-значений атрибутов). """
        pass


class CloneFactory:
    """ Фабрика клонирования объектов блоков данных для очередей (реализация паттерна Прототип). """
    # todo Возможно, избыточный класс
    def __init__(self, prototype: CloneInterface):
        # Инициация фабрики прототипом.
        self.__prototype: CloneInterface = prototype

    def clone(self):
        """ Клонировать блок данных. """
        return self.__prototype.clone()


class StageControlCommands(CloneInterface, ValueCopyInterface):
    """
    Команда на работу двигателей в определённый момент времени на определённый срок
    """
    def __init__(self, time_stamp:Optional[TimeStamp]=None, duration=0,
                 top_left=False, top_right=False,
                 down_left=False, down_right=False,
                 main=False):
        """

        :param time_stamp: отметка времени
        :param duration: длительность работы двигателя (зарезервировано на будущее)
        :param top_left: левый верхний двигатель работает?
        :param top_right: правый верхний двигатель работает?
        :param down_left: левый нижний двигатель работает?
        :param down_right: правый нижний двигатель работает?
        :param main: маршевый двигатель работает?
        """
        self.time_stamp = time_stamp
        # параметр "про запас", если будем делать в будущем длительность работы двигателей отличающейся от интервала
        # снятия показаний.
        self.duration: int = duration
        self.top_left = top_left
        self.top_right = top_right
        self.down_left = down_left
        self.down_right = down_right
        self.main = main

    def all_off(self)->bool:
        """
        Все двигатели выключены?

        """
        return not (self.top_left or self.top_right or self.down_left or self.down_right or self.main)

    def clone(self):
        return deepcopy(self)

    def data_copy(self, to_object: 'StageControlCommands'):
        to_object.time_stamp = self.time_stamp
        to_object.duration = self.duration
        to_object.top_left = self.top_left
        to_object.top_right = self.top_right
        to_object.down_left = self.down_left
        to_object.down_right =self.down_right
        to_object.main = self.main


class RealWorldStageStatusN(CloneInterface, ValueCopyInterface):
    """ Состояние ступени в конкретный момент времени """
    def __init__(self, position=None,
                 velocity=None,
                 acceleration=None,
                 orientation=None,
                 angular_velocity=0.,
                 angular_acceleration=0.,
                 time_stamp=0,
                 duration=0):
        """

        :param position: вектор положения издения в СКИП
        :type position: VectorComplex
        :param velocity: вектор линейной скорости
        :type velocity: VectorComplex
        :param acceleration: вектор линейного ускорения
        :type acceleration: VectorComplex
        :param orientation: ориентация (положительно - против часовой стрелки), рад
        :type orientation: VectorComplex
        :param angular_velocity: угловая скорость (положительно - против часовой стрелки)
        :type angular_velocity: float
        :param angular_acceleration: угловое ускорение (положительно - против часовой стрелки)
        :type angular_acceleration: float
        :param time_stamp: метка времени в миллисекундах
        :type time_stamp: int
        :param duration: длительность действия данного состояния, миллисекунд. Для использования в модуле отображения.
        :type duration: int
        """
        # Линейные положение, линейная скорость и ускорение - всё это в СКИП
        # self.position = position if position is not None else VectorComplex.get_instance()
        self.position = position or VectorComplex.get_instance()
        # self.velocity = velocity if velocity is not None else VectorComplex.get_instance()
        self.velocity = velocity or VectorComplex.get_instance()
        # зачем мне предыщущее значение ускорения??? Для рассчёта ускорения ускорения?
        # self.acceleration = acceleration if acceleration is not None else VectorComplex.get_instance()
        self.acceleration = acceleration or VectorComplex.get_instance()
        # Ориентация, угловая скорость и угловое ускорение - в СКЦМ
        # if orientation is None:
        #     self.orientation = VectorComplex.get_instance(0., 0.)
        # else:
        #     self.orientation = orientation
        # self.orientation = orientation if orientation is not None else VectorComplex.get_instance()
        self.orientation = orientation or VectorComplex.get_instance()
        self.angular_velocity = angular_velocity
        # Аналогично, зачем мне предыдущее угловое ускорение?
        self.angular_acceleration = angular_acceleration
        # предыдущее значение времени, необходимо для расчёта времменнОго интервала между двумя отсчётами
        self.time_stamp: int = time_stamp
        # Длительность действия этих параметров
        # todo убрать за ненадобностью, так как длительность можно вычислить по разнице между временнЫми метками
        # self.duration = duration


    def clone(self):
        return deepcopy(self)

    def data_copy(self, target_object: 'RealWorldStageStatusN'):
        target_object.position.decart = self.position.decart
        target_object.velocity.decart = self.velocity.decart
        target_object.acceleration.decart = self.acceleration.decart
        target_object.orientation.decart = self.orientation.decart
        target_object.angular_velocity = self.angular_velocity
        target_object.angular_acceleration = self.angular_acceleration
        target_object.time_stamp = self.time_stamp

class ReinforcementValue(CloneInterface, ValueCopyInterface):
    """
    Класс величины подкрепления для передачи через очередь между нитями
    """
    def __init__(self, time_stamp: int, reinforcement: float):
        self.time_stamp = time_stamp
        self.reinforcement = reinforcement

    def get_reinforcement(self):
        return self.time_stamp, self.reinforcement

    def clone(self):
        return deepcopy(self)

    def data_copy(self, target_object: 'ReinforcementValue'):
        target_object.time_stamp = self.time_stamp
        target_object.reinforcement = self.reinforcement


# примитивные данные для передачи через очередь (для проверок runtime)
NumR: Tuple = tuple([int, float, bool])
# примитивные данные для передачи через очередь (для проверок статическими анализаторами)
NumT = Union[int, float, bool]
# N = TypeVar('N', int, float, bool)


class QueueBlock:
    # Базовый класс блока данных передаваемого через очередь
    def __init__(self, test_id: Optional[TestId]):
        # Идентификатор испытания
        self._test_id: Optional[TestId] = test_id
        # Флаг используемости: блок пуст (не несёт данных) или полон (несёт данные)
        self._is_void: bool = True

    @property
    def test_id(self) -> Optional[TestId]:
        return self._test_id

    @test_id.setter
    def test_id(self, value: Optional[TestId]) -> None:
        self._test_id = value

    @property
    def is_void(self) -> bool:
        return self._is_void

    @is_void.setter
    def is_void(self, value: bool) -> None:
        self._is_void = value


class StageState(QueueBlock, RealWorldStageStatusN):
    """ Блок данных о состоянии изделия. """
    def __init__(self, test_id:Optional[TestId]=None):
        QueueBlock.__init__(self, test_id)
        RealWorldStageStatusN.__init__(self)


class ControlCommands(QueueBlock, StageControlCommands):
    """ Блок данных с командами управления. """
    def __init__(self, test_id:Optional[TestId]=None, time_stamp:Optional[TimeStamp]=None):
        QueueBlock.__init__(self, test_id)
        StageControlCommands.__init__(self)


class MessageBase(QueueBlock):
    """ Базовый класс информационного сообщения примитивного типа (int, float, bool ets.) для передачи через очередь. """
    def __init__(self, value: Optional[NumT]=None, test_id:Optional[TestId]=None):
        super().__init__(test_id)
        self._value: Optional[NumT] = value

    @property
    def value(self) -> Optional[NumT]:
        return self._value

    @value.setter
    def value(self, val: NumT):
        self._value = val


class BatchSizeMessage(MessageBase):
    def __init__(self, value: Optional[int]=None, test_id: Optional[TestId]=None):
        super().__init__(value, test_id)


class ReinforcementMessage(MessageBase):
    def __init__(self, value: Optional[float]=None, test_id: Optional[TestId]=None):
        super().__init__(value, test_id)


# DataType = Type[Union[ValueCopyInterface, NumT]]
# ContainerType = Type[QueueBlock]
#
#
# class DataAndContainers:
#     """ Класс двустороннего словаря, для хранения связей между блоками данных и их контейнерами. Синглтон. """
#     # ссылка на объект Синглтон
#     __this_object: Optional['DataAndContainers'] = None
#     # ключ для закрытия метода __init__
#     __create_key = object()
#
#     def __init__(self, create_key: object):
#         assert (create_key is DataAndContainers.__create_key), \
#             "DataAndContainers object must be created using get_instanse method."
#
#         # словарь "блок данных - контейнер"
#         self.__dict_1: Dict[DataType, ContainerType] = dict()
#         # словарь "контейнер - блок данных"
#         self.__dict_2: Dict[ContainerType, DataType] = dict()
#
#     @classmethod
#     def get_instanse(cls) -> 'DataAndContainers':
#         if cls.__this_object is None:
#             cls.__this_object = DataAndContainers(cls.__create_key)
#
#         return cls.__this_object
#
#     @overload
#     def add_link(self, type_dict: Dict[DataType, ContainerType]) -> None:
#         """ Добавить связь через словарь вида 'тип груза - тип контейнера'
#
#         :param type_dict: словарь типов вида 'тип груза - тип контейнера'"""
#         ...
#
#     @overload
#     def add_link(self, cargo_type: DataType, container_type: ContainerType) -> None:
#         """ Добавить связть парой 'тип груза - тип контейнера'
#
#         :param cargo_type: Тип груза.
#         :param container_type: Тип контейнера.
#         """
#         ...
#
#     def add_link(self, type_dict: Optional[Dict[DataType, ContainerType]], cargo_type: Optional[DataType]=None, container_type: Optional[ContainerType]=None) -> None:
#         """ Добавить связь (либо одной парой значений, либо кортежем).
#
#         :param type_dict: Словарь вида 'тип груза - тип контейнера'
#         :param cargo_type: Тип груза.
#         :param container_type: Тип контейнера.
#         """
#         if type_dict is not None:
#             for key in type_dict.keys():
#                 self.__dict_1[key] = type_dict[key]
#                 self.__dict_2[type_dict[key]] = key
#         else:
#             self.__dict_1[cargo_type] = container_type
#             self.__dict_2[container_type] = cargo_type
#
#     @overload
#     def get_link(self, cargo_type: DataType) -> ContainerType:
#         """ Получить связть 'тип груза - тип контейнера' """
#         ...
#
#     @overload
#     def get_link(self, container_type: ContainerType) -> DataType:
#         """ Получить связь 'тип контейнера - тип груза' """
#         ...
#
#     def get_link(self, any_type: Union[DataType, ContainerType]) ->  Union[ContainerType, DataType]:
#         """ Получить связь 'тип контейнера - тип груза', либо 'тип груза - тип контейнера'
#
#         :param any_type: Тип груза (или тип контейнера)
#         :return: Тип контейнера (или тип груза)
#         """
#         if issubclass(any_type, QueueBlock):
#             return self.__dict_2[any_type]
#         else:
#             return self.__dict_1[any_type]