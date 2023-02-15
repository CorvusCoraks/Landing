from point import VectorComplex
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Union, Any, TypeVar, Dict


QueueContent = Union['StageControlCommands', 'RealWorldStageStatusN', 'ReinforcementValue']
T = TypeVar('T', 'RealWorldStageStatusN', 'StageControlCommands', 'ReinforcementValue')


class CloneInterface(ABC):
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
    def __init__(self, time_stamp: int, duration=0,
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
        self.position = position or VectorComplex.get_instance()
        self.velocity = velocity or VectorComplex.get_instance()
        # зачем мне предыщущее значение ускорения??? Для рассчёта ускорения ускорения?
        self.acceleration = acceleration or VectorComplex.get_instance()
        # Ориентация, угловая скорость и угловое ускорение - в СКЦМ
        # todo с какой целью ориентация в виде вектора?
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
