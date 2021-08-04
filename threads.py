""" Класс нитей и инструментов работы с ними. """
from point import VectorComplex
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from physics import BigMap, HistoricData, RealWorldStageStatus
from queue import Queue
import cmath


class KillNeuroNetThread:
    """ Флаг-команда завершения нити. """
    def __init__(self, kill: bool):
        self.__value = kill

    @property
    def kill(self):
        return self.__value

    @kill.setter
    def kill(self, value: bool):
        self.__value = value


class KillRealWorldThread:
    """ Флаг-команда завершения нити. """
    def __init__(self, kill: bool):
        self.__value = kill

    @property
    def kill(self):
        return self.__value

    @kill.setter
    def kill(self, value: bool):
        self.__value = value


class Transform():
    """
    Изменение положения объекта (точки).
    """
    # Класс данных для передачи информации через очередь в окно отрисовки ситуации
    # Данные передаются уже в готовом виде в системе координат канвы в виде точек положения. По факту,
    # в виде фотоснимка. То есть, никакой дополнительной обработки данные не требуют.
    def __init__(self, vector2d: VectorComplex, orientation2d: VectorComplex, text: str):
        """

        :param vector2d: вектор нового положения центра масс объекта в системе координат канвы
        :param orientation2d: вектор новой ориентации объекта в системе координат канвы
        :param text: строка допоплнительной информации
        """
        self.vector2d = vector2d
        self.orientation2d = orientation2d
        self.text = text


class StageStatus:
    """
    Параметры ступени в конкретный момент времени в СКИП. Для передачи данных из нити физического моделирования.
    """
    # максимально возможное значение ежесекундного счётчика
    # Должно быть БОЛЬШЕ раза в два-три чем размер батча нейросети, чтобы в батче не оказалось одинаковых временных
    # меток
    maxCounterValue: int = 1023
    # максимальное существующее значение счётчика, которое должно быть меньше или равно максимально возможного
    currentTimerCounter: int = 1023

    def __init__(self, axisVector2d: VectorComplex, positionVector2d: VectorComplex, text: str):
        """

        :param axisVector2d: осевой вектор
        :param positionVector2d: позиция центра масс в СКИП
        :param text: строка дополнительной информации
        """
        self.axisVector2d = axisVector2d
        self.positionVector2d = positionVector2d
        self.text = text
        self.timerCounter: int
        # timerCounter - счётчик ++1, чтобы не путаться с очерёдностью данных.
        # первое значение счётчика после инициализации первого элемента очереди из 1023 превратится в 0
        # по достижению максимального значения, следующим шагом счётчик обнуляется
        # т. е. счётчик идёт от нуля до максимальной величины, обнуляется и цикл повторяется
        if StageStatus.currentTimerCounter == StageStatus.maxCounterValue:
            self.timerCounter = StageStatus.currentTimerCounter = 0
        else:

            StageStatus.currentTimerCounter += 1
            self.timerCounter = StageStatus.currentTimerCounter


# class ThreadsConnector:
#     """ Класс организующий перемещение данных между очередями, связывающими различные нити """
#     def __init__(self, fromReality: Queue, toReality: Queue, toCanvas: Queue):
#         """
#
#         :param fromReality: очередь данных из реальности (параметры ступени, подкрепление и пр.)
#         :param toReality: управляющие команды нейросети
#         :param toCanvas: данные из реальности для иллюстрирования процесса на канве
#         """
#         self.__fromReality = fromReality
#         self.__toReality = toReality
#         self.__toCanvas = toCanvas
#
#


def reality_thread(queue: Queue, killReality: KillRealWorldThread, killNeuro: KillNeuroNetThread):
    """
    Функция моделирующая поведение ступени в реальной физической среде
    :return:
    """
    print("Вход в нить окружающей среды.")
    # Блок имитационных данных для отображения
    # начальная ориентация объекта в системе координат канвы
    # orientation = VectorComplex.getInstance(0., -1.)
    # начальное состояние ступени в СКИП
    previousStatus = RealWorldStageStatus(position=BigMap.startPointInPoligonCoordinates,
                                          orientation=VectorComplex.getInstance(0., 1.))
    # HistoricData.previousOrientation = VectorComplex.getInstance(0., -1.)
    # HistoricData.previousPosition = VectorComplex.getInstance(BigMap.width/2, 20)

    # пока в тестовых целях сделано через счётчик i
    # в дальнейшем сделать исключительно через флаги kill
    i = 0
    while not killReality.kill:
        # КОД

        # new_orientation = VectorComplex.getInstance()
        # новое состояние в СКИП
        newStatus = RealWorldStageStatus()
        # новая ориентация
        # сложение двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        # new_orientation.cardanus = HistoricData.previousOrientation.cardanus * cmath.rect(1., (cmath.pi / 36))
        newStatus.orientation.cardanus = previousStatus.orientation.cardanus * cmath.rect(1., (- cmath.pi / 36))
        # новое положение ступени в СКИП
        # newPosition = VectorComplex.getInstance(BigMap.width/2, 20 + i * 1)
        # newPosition = VectorComplex.getInstance(HistoricData.previousPosition.x, HistoricData.previousPosition.y +i *1)
        newStatus.position = VectorComplex.getInstance(previousStatus.position.x, previousStatus.position.y - i * 1)
        # преобразование из СКИП в СКК
        inCanvasCoordSystem = RealWorldStageStatus()
        # (inCanvasCoordSystem.orientation, inCanvasCoordSystem.position) = pointsListToNewCoordinateSystem(
        #     [newStatus.orientation, newStatus.position],
        #     VectorComplex.getInstance(- BigMap.testPoligonOriginInCCS.x, BigMap.testPoligonOriginInCCS.y),
        #     0., True
        # )
        (inCanvasCoordSystem.orientation, inCanvasCoordSystem.position) = pointsListToNewCoordinateSystem(
            [newStatus.orientation, newStatus.position],
            BigMap.canvasOriginInPoligonCoordinates,
            0., True
        )
        # добавить в выходную очередь очередную порцию информации о состоянии ступени
        print ("№{0}, new orient: {1}, position: {2}".format(i, newStatus.orientation, inCanvasCoordSystem.position))
        # queue.put(StageStatus(inCanvasCoordSystem.orientation, inCanvasCoordSystem.position, "Команда №{}".format(i)))
        # queue.put(Transform(VectorComplex.getInstance(BigMap.width/2, 20 + i * 1), new_orientation, "Команда №{}".format(i)))
        queue.put(Transform(inCanvasCoordSystem.position, inCanvasCoordSystem.orientation, "Команда №{}".format(i)))

        # запоминаем позицию
        # HistoricData.previousPosition = newPosition
        previousStatus.position = newStatus.position
        # запоминаем ориентацию, для использования в следующей итерации
        # orientation = new_orientation
        # HistoricData.previousOrientation = new_orientation
        previousStatus.orientation = newStatus.orientation

        # КОД
        if i == 80:
            killReality.kill = True
        i += 1
    else:
        killNeuro.kill = True


# фунция нити нейросети
def neuronet_thread(queue: Queue, killThisThread: KillNeuroNetThread):
    """
    Метод, запускаемый в отдельной нитке для обучения нейросети.

    :param queue: очередь, для передачи даннных в модуль визуализации
    :return:
    """
    print("Вход в нить нейросети.")
    # заглушка, чтобы эта функция не работала
    return
    #
    # запуск метода обучения сети
    # start_nb(frameRate)
    # получить новое положение и ориентацию объекта
    #
    # преобразовать положение и ориентацию объекта из системы координат пространства в систему координат канвы
    #
    # отправить новое положение и ориентацию (в системе координат канвы) в нить вывода
    # queue.put(Transform(Point(), Point(), ''))
    #
    # Блок имитационных данных для отображения
    # начальная ориентация объекта в системе координат канвы
    orientation = VectorComplex.getInstance(0., -1.)
    for i in range(80):
    # while not killNeuronetThread:
        # new_orientation = Point()
        new_orientation = VectorComplex.getInstance()
        # АХТУНГ!
        # В левой системе координат (система координат канвы) положительный угол поворота - по часовой стрелке!
        # Т. е., положительный угол поворота,
        # это угол поворота от положительной полуоси абцисс к положительной полуоси ординат
        # новая ориентация
        # сложение двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        new_orientation.cardanus = orientation.cardanus * cmath.rect(1., (cmath.pi / 36))
        # отправляем новое абсолютное положение в системе координат канвы и абсолютный угол (относительно положительной
        # полуоси абцисс) ориентации объекта в очередь
        # queue.put(Transform(Point(55, 20 + i * 10), new_orientation, "Команда №{}".format(i)))
        queue.put(Transform(VectorComplex.getInstance(BigMap.width/2, 20 + i * 1), new_orientation, "Команда №{}".format(i)))
        # запоминаем ориентацию, для использования в следующей итерации
        orientation = new_orientation

        if killThisThread.kill:
            print("Завершение нити нейросети.")
            break


# def fromTPCStoCCS(status: StageStatus):
#     """
#     Функция перобразования данных из очереди физической модели в данные очереди канвы
#
#     :param status: очередное состояние ступени
#     """
#     # todo убрать за ненадобностью
#     # преобразовать вектора из СКИП в СКК
#     position = complexChangeSystemCoordinatesUniversal(status.positionVector2d,
#                                                        VectorComplex.getInstance(- BigMap.testPoligonOriginInCCS.x,
#                                                                                  BigMap.testPoligonOriginInCCS.y),
#                                                        0,
#                                                        True)
#     verticalAxis = complexChangeSystemCoordinatesUniversal(status.axisVector2d,
#                                                            VectorComplex.getInstance( - BigMap.testPoligonOriginInCCS.x,
#                                                                                       BigMap.testPoligonOriginInCCS.y),
#                                                            0,
#                                                            True)
#     return Transform(position, verticalAxis, "text")
