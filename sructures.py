from point import VectorComplex

class StageControlCommands:
    """
    Команда на работу двигателей в определённый момент времени на определённый срок
    """
    def __init__(self, timeStamp: int, duration: int,
                 topLeft=False, topRight=False,
                 downLeft=False, downRight=False,
                 main=False):
        timeStamp = timeStamp
        duration = duration
        topLeft = topLeft
        topRight = topRight
        downLeft = downLeft
        downRight = downRight
        main = main


class RealWorldStageStatusN():
    """ Состояние ступени в конкретный момент времени """
    def __init__(self, position=None,
                 velocity=None,
                 axeleration=None,
                 orientation=None,
                 angularVelocity=0.,
                 angularAxeleration=0.,
                 timeStamp=0):
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
        :param timeStamp: метка времени в микросекундах
        :type timeStamp: int
        """
        # Линейные положение, линейная скорость и ускорение - всё это в СКИП
        self.position = position if position is not None else VectorComplex.getInstance()
        self.velocity = velocity if velocity is not None else VectorComplex.getInstance()
        # зачем мне предыщущее значение ускорения??? Для рассчёта ускорения ускорения?
        self.axeleration = axeleration if axeleration is not None else VectorComplex.getInstance()
        # Ориентация, угловая скорость и угловое ускорение - в СКЦМ
        # if orientation is None:
        #     self.orientation = VectorComplex.getInstance(0., 0.)
        # else:
        #     self.orientation = orientation
        self.orientation = orientation if orientation is not None else VectorComplex.getInstance()
        self.angularVelocity = angularVelocity
        # Аналогично, зачем мне предыдущее угловое ускорение?
        self.angularAxeleration = angularAxeleration
        # предыдущее значение времени, необходимо для расчёта времменнОго интервала между двумя отсчётами
        self.timeStamp: int = timeStamp
        # Длительность действия этих параметров, сек
        # todo убрать и перейти на timeStamp
        # self.timeLength = timeLength
        # todo использовать или previousTimeStamp, или timeLength. Одновременно, скорее всего излишне.

    def lazyCopy(self):
        newObject = RealWorldStageStatusN()
        newObject.position = self.position.lazyCopy()
        newObject.velocity = self.velocity.lazyCopy()
        newObject.axeleration = self.axeleration.lazyCopy()
        newObject.orientation = self.orientation.lazyCopy()
        newObject.angularVelocity = self.angularVelocity
        newObject.angularAxeleration = self.angularAxeleration
        newObject.timeStamp = self.timeStamp
        # newObject.timeLength = self.timeLength
        return newObject