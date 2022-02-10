""" Класс нитей и инструментов работы с ними. """
import physics
from point import VectorComplex
from decart import complexChangeSystemCoordinatesUniversal, pointsListToNewCoordinateSystem
from physics import BigMap, HistoricData, RealWorldStageStatus, Moving
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
    # Передаются данные конкретного момента времени.
    # todo в перспективе класс удалить. Все данные передавать в очередь через класс RealWorldStageStatus
    def __init__(self, vector2d: VectorComplex, orientation2d: VectorComplex, lineVelocity: VectorComplex, text: str, stageStatus: RealWorldStageStatus):
        """

        :param vector2d: вектор нового положения центра масс объекта в системе координат полигона
        :param orientation2d: вектор новой ориентации объекта в системе координат полигона
        :param lineVelocity: вектор линейной скорости
        :param text: строка допоплнительной информации
        """
        self.vector2d = vector2d
        self.orientation2d = orientation2d
        self.lineVelocity = lineVelocity
        self.text = text
        # todo в перспективе, передавать информацию через нить именно через этот объект, а не через Transform
        self.stageStatus = stageStatus


class StageStatus:
    """
    Параметры ступени в конкретный момент времени в СКИП. Для передачи данных из нити физического моделирования.
    """
    # todo Возможно, класс не нужен
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
    # начальное состояние ступени в СКИП
    # previousStatusTest = RealWorldStageStatus(position=BigMap.startPointInPoligonCoordinates,
    #                                                orientation=VectorComplex.getInstance(0., 1.))

    physics.previousStageStatus = RealWorldStageStatus(position=BigMap.startPointInPoligonCoordinates,
                         orientation=VectorComplex.getInstance(0., 1.),
                         velocity=VectorComplex.getInstance(0., -10))

    # newStatus = RealWorldStageStatus()
    # пока в тестовых целях сделано через счётчик i
    # в дальнейшем сделать исключительно через флаги kill
    i = 0
    while not killReality.kill:
        # КОД
        # новое состояние в СКИП
        # newStatus = RealWorldStageStatus()
        # # новая ориентация
        # # сложениself.orientation = orientationе двух углов: старой, абсолютной ориентации плюс новое изменение (дельта) угла
        # newStatus.orientation.cardanus = previousStatusTest.orientation.cardanus * cmath.rect(1., (- cmath.pi / 36))
        # # приводим к единичному вектору
        # newStatus.orientation.cardanus = newStatus.orientation.cardanus / abs(newStatus.orientation.cardanus)
        # # новое положение ступени в СКИП
        # newStatus.position = VectorComplex.getInstance(previousStatusTest.position.x, previousStatusTest.position.y - i * 1)

        newStageStatus = Moving.getNewStatus()
        physics.previousStageStatus = newStageStatus
        print("{0} Posititon: {1}, Velocyty: {2},\n Axelerantion: {3}, Orientation: {4}".
              format(i, newStageStatus.position, newStageStatus.velocity,
                     newStageStatus. axeleration, newStageStatus.orientation))

        # добавить в выходную очередь очередную порцию информации о состоянии ступени

        # Для отправки в очередь создаём объект с независимыми новыми чистыми атрибутами.
        # Т. е. Объект в очереди теперь не подвержен случайному изменению из вне очереди.
        # Иными словами, если захочется изменить объект в очереди, теперь придётся сначала извлечь его из очереди,
        # для того, чтобы получить к нему доступ.
        # queue.put(Transform(newStatus.position.lazyCopy(),
        #                     newStatus.orientation.lazyCopy(),
        #                     "Команда №{}".format(i)))
        queue.put(Transform(newStageStatus.position.lazyCopy(),
                            newStageStatus.orientation.lazyCopy(),
                            newStageStatus.velocity.lazyCopy(),
                            "Команда №{}".format(i),
                            newStageStatus.lazyCopy()))
        # print("{0} Put. Posititon: {1}, Orientation: {2}".format(i, newStatus.position, newStatus.orientation))
        # # запоминаем позицию
        # previousStatusTest.position = newStatus.position
        # # запоминаем ориентацию, для использования в следующей итерации
        # previousStatusTest.orientation = newStatus.orientation

        # newStatus = RealWorldStageStatus()

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