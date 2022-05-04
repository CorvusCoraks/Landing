from point import VectorComplex

class StageControlCommands:
    """
    Команда на работу двигателей в определённый момент времени на определённый срок
    """
    def __init__(self, timeStamp: int, duration=0,
                 topLeft=False, topRight=False,
                 downLeft=False, downRight=False,
                 main=False):
        self.timeStamp = timeStamp
        # параметр "про запас", если будем делать в будущем длительность работы двигателей отличающейся от интервала
        # снятия показаний.
        self.duration: int = duration
        self.topLeft = topLeft
        self.topRight = topRight
        self.downLeft = downLeft
        self.downRight = downRight
        self.main = main

    def allOff(self)->bool:
        """
        Все двигатели выключены?

        """
        return not (self.topLeft or self.topRight or self.downLeft or self.downRight or self.main)

class RealWorldStageStatusN():
    """ Состояние ступени в конкретный момент времени """
    def __init__(self, position=None,
                 velocity=None,
                 axeleration=None,
                 orientation=None,
                 angularVelocity=0.,
                 angularAxeleration=0.,
                 timeStamp=0,
                 duration=0):
        """

        :param position: вектор положения издения в СКИП
        :type position: VectorComplex
        :param velocity: вектор линейной скорости
        :type velocity: VectorComplex
        :param axeleration: вектор линейного ускорения
        :type axeleration: VectorComplex
        :param orientation: ориентация (положительно - против часовой стрелки), рад
        :type orientation: VectorComplex
        :param angularVelocity: угловая скорость (положительно - против часовой стрелки)
        :type angularVelocity: float
        :param angularAxeleration: угловое ускорение (положительно - против часовой стрелки)
        :type angularAxeleration: float
        :param timeStamp: метка времени в миллисекундах
        :type timeStamp: int
        :param duration: длительность действия данного состояния, миллисекунд. Для использования в модуле отображения.
        :type duration: int
        """
        # Линейные положение, линейная скорость и ускорение - всё это в СКИП
        # self.position = position if position is not None else VectorComplex.getInstance()
        self.position = position or VectorComplex.getInstance()
        # self.velocity = velocity if velocity is not None else VectorComplex.getInstance()
        self.velocity = velocity or VectorComplex.getInstance()
        # зачем мне предыщущее значение ускорения??? Для рассчёта ускорения ускорения?
        # self.axeleration = axeleration if axeleration is not None else VectorComplex.getInstance()
        self.axeleration = axeleration or VectorComplex.getInstance()
        # Ориентация, угловая скорость и угловое ускорение - в СКЦМ
        # if orientation is None:
        #     self.orientation = VectorComplex.getInstance(0., 0.)
        # else:
        #     self.orientation = orientation
        # self.orientation = orientation if orientation is not None else VectorComplex.getInstance()
        self.orientation = orientation or VectorComplex.getInstance()
        self.angularVelocity = angularVelocity
        # Аналогично, зачем мне предыдущее угловое ускорение?
        self.angularAxeleration = angularAxeleration
        # предыдущее значение времени, необходимо для расчёта времменнОго интервала между двумя отсчётами
        self.timeStamp: int = timeStamp
        # Длительность действия этих параметров
        # todo убрать за ненадобностью, так как длительность можно вычислить по разнице между временнЫми метками
        # self.duration = duration

    def lazyCopy(self):
        newObject = RealWorldStageStatusN()
        newObject.position = self.position.lazyCopy()
        newObject.velocity = self.velocity.lazyCopy()
        newObject.axeleration = self.axeleration.lazyCopy()
        newObject.orientation = self.orientation.lazyCopy()
        newObject.angularVelocity = self.angularVelocity
        newObject.angularAxeleration = self.angularAxeleration
        newObject.timeStamp = self.timeStamp
        # newObject.duration = self.duration
        return newObject

class ReinforcementValue:
    """
    Класс величины подкрепления для передачи через очередь между нитями
    """
    def __init__(self, timestamp: int, reinforcement: float):
        self.timestamp = timestamp
        self.reinforcement = reinforcement

    def getReinforcement(self):
        return self.timestamp, self.reinforcement

    # @property
    # def reinforcement(self):
    #     return self.reinforcement