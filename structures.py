from point import VectorComplex
from abc import ABC, abstractmethod
from copy import deepcopy


class CloneInterface(ABC):
    @abstractmethod
    def clone(self):
        """ Клонирование объекта (реализация паттерна Прототип). """
        pass


class CloneFactory:
    """ Фабрика клонирования объектов блоков данных для очередей (реализация паттерна Прототип). """
    def __init__(self, prototype: CloneInterface):
        # Инициация фабрики прототипом.
        self.__prototype: CloneInterface = prototype

    def clone(self):
        """ Клонировать блок данных. """
        return self.__prototype.clone()


class StageControlCommands(CloneInterface):
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

    # def lazy_copy(self) -> 'StageControlCommands':
    #     return StageControlCommands(deepcopy(self.time_stamp))

    def clone(self):
        return deepcopy(self)


class RealWorldStageStatusN(CloneInterface):
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

    # def lazy_copy(self) -> 'RealWorldStageStatusN':
    #     # todo метод ликвидировать. везде перевести на deepcopy()
    #     newObject = RealWorldStageStatusN()
    #     newObject.position = self.position.lazy_copy()
    #     newObject.velocity = self.velocity.lazy_copy()
    #     newObject.acceleration = self.acceleration.lazy_copy()
    #     newObject.orientation = self.orientation.lazy_copy()
    #     newObject.angular_velocity = self.angular_velocity
    #     newObject.angular_acceleration = self.angular_acceleration
    #     newObject.time_stamp = self.time_stamp
    #     # newObject.duration = self.duration
    #     return newObject

    def clone(self):
        return deepcopy(self)


class ReinforcementValue(CloneInterface):
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

    # @property
    # def reinforcement(self):
    #     return self.reinforcement
