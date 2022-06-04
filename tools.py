from point import VectorComplex
from math import fabs
# from stage import BigMap
from stage import Sizes, BigMap
from structures import RealWorldStageStatusN, StageControlCommands, ReinforcementValue
from abc import ABC, abstractmethod
from queue import Queue
from typing import Union, TypeVar
from copy import deepcopy
# Разные утилиты

# Тип: классы объектов данных, которые передаются через очереди
QueueMembers = TypeVar('QueueMembers', RealWorldStageStatusN, StageControlCommands, ReinforcementValue)

class MetaQueue:
    """ Класс содержащий в себе очереди передачи данных. Синглтон. """
    # Синглтон-объект
    __this_object: 'MetaQueue' = None
    # Ключ для реализации создания объекта исключительно через специальный метод класса
    __create_key = object()

    def __init__(self, create_key: object):
        assert (create_key == MetaQueue.__create_key), \
            "MetaQueue object must be created using getInstanse method."
        # Словарь с очередями
        self.__queues_dict: dict = {
            "area": Queue(), # очередь сообщений для испытательного полигона
            "stage": Queue(), # очередь сообщений для вида изделия
            "info": Queue(), # очередь сообщений для информационного блока
            "neuro": Queue(), # очередь сообщений для нейросети
            "reinf": Queue(), # очередь сообщений с подкреплениями
            "command": Queue() # очередь сообщений с управляющими воздействиями
        }

    @classmethod
    def getInstance(cls) -> 'MetaQueue':
        """ Метод возвращает объект данного типа. Если объект не существует, то создаёт его перед этим. """
        if MetaQueue.__this_object is None:
            MetaQueue.__this_object = MetaQueue(MetaQueue.__create_key)

        return MetaQueue.__this_object

    def put(self, value: QueueMembers):
        """ Метод добавки блока данных в соответствующие очереди """
        # в какую очередь добавлять, определяется по типу добавляемых данных
        if isinstance(value, RealWorldStageStatusN):
            self.__queues_dict["area"].put(deepcopy(value))
            self.__queues_dict["stage"].put(deepcopy(value))
            self.__queues_dict["info"].put(deepcopy(value))
            self.__queues_dict["neuro"].put(deepcopy(value))
        elif isinstance(value, StageControlCommands):
            self.__queues_dict["command"].put(deepcopy(value))
        else:
            self.__queues_dict["reinf"].put(deepcopy(value))

    def get_queue(self, name: str) -> Queue:
        """ Получить очередь по её имени. """
        if name in self.__queues_dict.keys():
            return self.__queues_dict[name]
        else:
            raise ValueError('MetaQueue Object: name="{0}" argument is not valid key of queues dict'.format(name))






# class SectorBorders:
#     @classmethod
#     def getCircleBorders(cls):
#         return (1, 10, 100, 10000, 100000)
#
#     @classmethod
#     def getAltitudeBorders(cls):
#         return (1, 5, 50, 5000, 50000)
#
#     @classmethod
#     def getPeriodBorders(cls):
#         return (1, 10, 100, 1000, 10000, 60000)
#
#     @classmethod
#     def getReinforcementBorders(cls):
#         return ()

class Reinforcement():
    """
    Класс подкрепления.

    """
    # Предварительно.
    # 1. Разбить пространство на зоны / квадраты.
    # 2. При попадании в квадрат, актор получает подкрепление.
    # 3. Подкрепление тем выше, чем ближе изделие к точке посадки.
    # -. Учитываются только переходы от зоны с низким подкреплением в зону с высоким подкреплением,
    # при обратном переходе, подкрепление - ноль.
    # -. Подкрепление в квадрате делится на время, сколько работали двигатели в предыдущем квадрате, таким образом,
    # чем меньше работали двигатели, тем выше подкрепление.
    # -. При повторном переходе из зоны с низким подкреплением в зону с высоким,
    # 4. При попадании изделия в некую окрестность точки посадки,
    # производится проверка на вписывание в динамические параметры по типу "не больше",
    # и назначется окончательное подкрепление.
    #
    # Вариант 1.
    # - Разбить пространство на концентрические сектора с единым центром в точке посадки.
    # - Концентрические сектора совпадают с границами диапазонов считывания данных.
    # - Максимальное время работы любого двигателя в рамках одного диапазона считывания данных - 10 секунд. Актуально
    # для больших диапазонов.
    # - Подкрепление для данного состояния прямо пропорционально базовому подкреплению и обратно пропорционально
    # времени работы маршевого и рулевых двигателей в предыдущем диапазоне считывания показаний. Т. е., если в данном
    # диапазоне считывания двигатели не работали, то подкрепление за проход этого диапазона будет максимально и равно
    # базовому.
    # - Установить подкрепление за посадку (с оговоренной погрешностью) - 0,3 (выход за пределы оговорённой
    # погрешности по любому параметру на 10% уменьшает данную величину подкрепления на 1%, на 20% - на 5%,
    # на 30% - на 10% и т. д. до нуля), а суммарное базовое подкрепление за весь процесс приземления - 0,7
    #
    # Вариант 2.
    # Логика: приближение к точке посадки должно поощеряться, работа двигателей должна наказываться.
    # - Если при переходе из одного состояния в другое происходит приближение к точке посадки - поощеряем.
    # - Если при переходе из одного состояния в другое радиус-вектор центра масс изделия
    # меньше самого короткого в данном испытании - поощеряем.
    # - Если при переходе из одного состояния в другое работают двигатели - уменьшаем поощерение.
    # Т. е.
    #

    # successLandingBase = 0.3
    # processBase = 1 - successLandingBase
    # минимальный вектор положения центра масс изделия, достигнутый в одном испытании
    minVector = VectorComplex.getInstance(float("inf"), float("inf"))

    accuracy = 0

    def __init__(self):
        pass

    @classmethod
    def getReinforcement(cls, stageStatus: RealWorldStageStatusN, jets: StageControlCommands):
        """
        Подкрепление

        :param stageStatus: состояние ступени
        :param jets: информация о работавших двигателях
        :return:
        """
        successReinforcement = 0.
        landingReinforcement = 0.
        if Finish.isOneTestFailed(stageStatus.position):
            cls.minVector = VectorComplex.getInstance(float("inf"), float("inf"))
            return 0

        # подкрепление за удачную посадку
        if Finish.isOneTestSuccess(stageStatus, cls.accuracy):
            # cls.minVector = VectorComplex.getInstance(float("inf"), float("inf"))
            successReinforcement = 100

        # подкрепление в процесс посадки
        # корректирующий подкрепление множитель
        mult = 0
        if abs(stageStatus.position) < abs(cls.minVector):
            # если достигли позиции ещё ближе, чем была самая близкая, то фиксируем данный радиус-вектор
            cls.minVector = stageStatus.position
            # собираем множитель, в зависимости от включённости двигателей
            mult =+ 1.25 if jets.topLeft else 0
            mult =+ 1.25 if jets.topRight else 0
            mult =+ 1.25 if jets.downLeft else 0
            mult =+ 1.25 if jets.downRight else 0
            mult =+ 5.0 if jets.main else 0
            # все одновременно работающие рулевые двигатели имеют "цену" одного работающего маршевого двигателя
            # считаем, с учётом работавших двигателей, понижая подкрепление
            landingReinforcement = 1 if mult == 0 else 10 / mult

            if Finish.isOneTestSuccess(stageStatus, cls.accuracy):
                cls.minVector = VectorComplex.getInstance(float("inf"), float("inf"))

        return successReinforcement + landingReinforcement


class Finish():
    """
    Класс завершения единичного испытания
    """

    # Допустимое отклонение при выявлении факта посадки (метров)
    __yEpsilon = 0.01
    # Высота выключения двигателей (по высоте центра масс)
    __legRelativeY = Sizes.massCenterFromLandingPlaneDistance

    # Необходим для того, чтобы единичное испытание не длилось чрезмерное неразумное время
    def __init__(self):
        pass

    @classmethod
    def isOneTestFailed(cls, coord: VectorComplex):
        """ Проверка на неблагополучное завершение очередной тренировки

        :param coord: центр масс ракеты в СКИП
        """
        # Очередная тренировка заканчивается либо удачной посадкой, либо ударом о землю,
        # либо выходом за пределы зоны испытаний
        # Метод необходим исключительно для того, чтобы одно испытание не длилось вечно
        #
        # poligonLegY = coord.y + self.__legRelativeY
        if fabs(coord.x) * 2 > BigMap.width \
            or coord.y > BigMap.height \
            or coord.y < cls.__legRelativeY - cls.__yEpsilon:
            # Если ступень вылетела за пределы испытательного полигона:
            # - ступень вылетела за левую/правую границу полигона
            # - вылетела за верхнюю границу полигона
            # - вылетела за нижнюю границу полигона
            # испытание завершено
            return True
        return False

    @classmethod
    def isOneTestSuccess(cls , state: RealWorldStageStatusN, accuracy: int, close=True)->bool:
        """
        Посадка завершена успешно. Уррраааа!

        :param state: состояние изделия
        :param accuracy: параметр выбранной точности, 0, 1, 2, ..., 9
        :param close: выбрать диапазон расчёта параметров: дальний (не очень точный) или ближний (точный)
        :type close: bool
        :return:
        """

        def within(accuracy: dict, value: float)->bool:
            """ Проверка на нахождение внутри диапазона """
            if accuracy["min"] < value < accuracy["max"]:
                return True
            else:
                return False

        accuracyDict = Finish.landingScope(accuracy, close)

        # Последовательная проверка по всем параметрам на успешность попадания в их диапазоны.
        if within(accuracyDict["dy"], state.position.y) and within(accuracyDict["dx"], state.position.x):
            if within(accuracyDict["dVy"], state.velocity.y) and within(accuracyDict["dVx"], state.velocity.x):
                if within(accuracyDict["dAy"], state.axeleration.y) and within(accuracyDict["dAx"], state.axeleration.x):
                    if within(accuracyDict["dPhi"], state.orientation):
                        if within(accuracyDict["dW"], state.angularVelocity):
                            if within(accuracyDict["dE"], state.angularAxeleration):
                                return True
        return False

    @classmethod
    def landingScope(cls, step: int, close=True)->dict:
        """
        Диапазоны параметров, в которые должно попасть изделие при штатной посадке

        :param step: одно из десяти значений: 0, 1, ..., 9, где 0 - максимальная точность, 9 - минимальная точность
        :param close: если True, выдаём значения высокой точности при нахождении у поверхности, если False - низкой.
        :type close: bool
        :return:
        """
        def soFar(x: int)->tuple:
            """ Линейная функция падающая от (9: 100) до (0; 1)

            :return: min - (-1, +1)
            """
            value = ((100 - 1) / 9) * x + 1
            return -value, +value


        def soClose(x: int)->tuple:
            """ Линейная функция, падающая от (9; 1) до (0; 0.01)

             :return: min - (-0.01, +0.01)
             """
            value = ((1 - 0.01) / 9) * x + 0.01
            return -value, +value

        result = soClose(step) if close else soFar(step)
        # Точность по X в максимуме будет (-5, +5), в минимуме - (-50000. +50000)
        resultX = (result[0] * 500, result[1] * 500)
        # Кооректировка к точности в максимуме будет +0,01, в минимуме +45000
        resultY = result[1] if close else result[1] * 50 * step

        return {
                # допустимый диапазон положения по оси Y
                "dy": {"min": cls.__legRelativeY, "max": cls.__legRelativeY + resultY},
                # допустимый диапазон положения по оси Х
                "dx": {"min": resultX[0], "max": resultX[1]},
                # допустимый диапазон линейной скорости по оси Y
                "dVy": {"min": result[0], "max": result[1]},
                # допустимый диапазон линейной скорости по оси X
                "dVx": {"min": result[0], "max": result[1]},
                # допустимый диапазон линейного ускорения по оси Y
                "dAy": {"min": result[0], "max": result[1]},
                # допустимый диапазон линейного ускорения по оси Х
                "dAx": {"min": result[0], "max": result[1]},
                # допустимый диапазон угла ориентации
                "dPhi": {"min": result[0], "max": result[1]},
                # допустимый диапазон угловой скорости
                "dW": {"min": result[0], "max": result[1]},
                # допустимый диапазон уголового ускорения
                "dE": {"min": result[0], "max": result[1]}
                }

def mathInt(value: float)->int:
    """
    Округление до целого по правилу математики.

    :param value: входное число с плавающей точкой
    :return: округлённое до целого
    """
    return int(value + (0.5 if value > 0 else -0.5))

# def onesAndZerosVariants(length:int)->list:
#     """ Функция возвращает ВСЕ варианты размещения (все комбинации) из множества [0; 1] по length штук
#
#     :param length: длинна списка, варианты расположения нулей и единиц в котором мы ищем
#     :return: список вида [[0, 0, 0], [0, 1, 0], ..., [1, 1, 1]]
#     """
#
#     # Суть работы функции.
#     # Везде нули - один вариант
#     # Единица ставится на первую позицию - второй вариант
#     # Единица смещается на вторую позицию - третий вариант.
#     # ...
#     # После прохода единицы до конца.
#     # Единица ставится на первую и вторую позиции - ещё вариант
#     # Вторая единица смещается на одну позицию вправо - ещё вариант
#     # ... и т. д. до упора вправо.
#     # Первая единица смещается вправо на одну позицию - ещё вариант
#     # ... и т. д. пока она не упрётся в единицу, достигшую правого края.
#     # Далее, слева ставятся три единицы и так же поочерёдно сдвигаются вправо, образуя новые варианты.
#     # ...
#     # И, последний вариант - все единицы
#
#     def oneTrip(start: int, stop: int, startStr: list, motherList: list):
#         """ Подпрограмма, выдающая ВСЕ варианты для конечного набора единиц, смещая их поочерёдно вправо
#
#         :param start: позиция, в которой стоит единица, которую мы будем двигать вправо
#         :param stop: позиция до которой мы будем двигать единицу (но не занимая эту позицию)
#         :param startStr: исходный список, в котором слева есть единицы, которые мы и должны поочерёдно сместить вправо
#         :param motherList: результирующий список, к которому мы последовательно добавляем получающиеся варианты
#         """
#
#         tempList = startStr.copy()
#         for i in range(start, stop):
#             tempList = tempList.copy()
#             if i+1 == stop:
#                 # если единица достигла правого края
#                 if start != 0:
#                     # и если слева от той позиции откуда эта единица стартовала ещё есть позиции с единицами
#                     # начинаем двигать её сестру, которая стояла слева от неё
#                     oneTrip(start-1, stop-1, tempList, motherList)
#                 return
#             else:
#                 # а если единица ещё не достигла правого свободного края
#                 # присваиваем её позиции ноль
#                 tempList[i] = 0.
#                 # а следующей позиции справа единицу, как бы сдвигая эту самую единицу на одну позицию вправо
#                 tempList[i+1] = 1.
#                 # пристыковываем полученный набор к результирующему списку
#                 motherList.append(tempList)
#
#     # список заготовка из нулевых элементов
#     zeroList: list = [x * 0 for x in range(length)]
#
#     # результат, собственно
#     result = []
#     # первый элемент результата - список из нулевых элементов
#     result.append(zeroList.copy())
#
#     for j in range(length):
#         startStr = zeroList.copy()
#         for m in range(j+1):
#             startStr[m] = 1.
#
#         # ^^^^ цикл, выдающий последовательно списки вида [1., 0., ..., 0.], [1., 1., ..., 0.], ..., [1., 1., ..., 1.]
#
#         start = j
#         stop = length
#
#         result.append(startStr)
#         oneTrip(start, stop, startStr, result)
#     return result

def onesAndZerosVariantsF(vectorLength: int, startPosition: int)->list:
    """ Функция возвращает ВСЕ варианты размещения (все комбинации) из множества [0; 1] в векторе длиной *vectorLength*


    Варианты расположения нулей и единиц в векторе начинаются с позиции *startPosition* включительно.
    До позиции *startPositon* в векторе находятся нули.

    :param vectorLength: длинна списка, варианты расположения нулей и единиц в котором мы ищем
    :param startPosition: позиция, до которой в векторе всегда находятся нули, с неё начинается присутствие нулей и ед.
    :return: список вида [[0, 0, 0, 0], [0, 0, 1, 0], ..., [0, 1, 1, 1]]
    """

    # Суть работы функции.
    # Везде нули - один вариант
    # Единица ставится на первую позицию - второй вариант
    # Единица смещается на вторую позицию - третий вариант.
    # ...
    # После прохода единицы до конца.
    # Единица ставится на первую и вторую позиции - ещё вариант
    # Вторая единица смещается на одну позицию вправо - ещё вариант
    # ... и т. д. до упора вправо.
    # Первая единица смещается вправо на одну позицию - ещё вариант
    # ... и т. д. пока она не упрётся в единицу, достигшую правого края.
    # Далее, слева ставятся три единицы и так же поочерёдно сдвигаются вправо, образуя новые варианты.
    # ...
    # И, последний вариант - все единицы

    def oneTrip(start: int, stop: int, startStr: list, startPoint: int, motherList: list):
        """ Подпрограмма, выдающая ВСЕ варианты для конечного набора единиц, смещая их поочерёдно вправо

        :param start: позиция, в которой стоит единица, которую мы будем двигать вправо
        :param stop: позиция до которой мы будем двигать единицу (но не занимая эту позицию)
        :param startStr: исходный список, в котором слева есть единицы, которые мы и должны поочерёдно сместить вправо
        :param motherList: результирующий список, к которому мы последовательно добавляем получающиеся варианты
        """

        tempList = startStr.copy()
        for i in range(start, stop):
            tempList = tempList.copy()
            if i + 1 == stop:
                # если единица достигла правого края
                if start != startPoint:
                    # и если слева от той позиции откуда эта единица стартовала ещё есть позиции с единицами
                    # начинаем двигать её сестру, которая стояла слева от неё
                    oneTrip(start - 1, stop - 1, tempList, startPoint, motherList)
                return
            else:
                # а если единица ещё не достигла правого свободного края
                # присваиваем её позиции ноль
                tempList[i] = 0.
                # а следующей позиции справа единицу, как бы сдвигая эту самую единицу на одну позицию вправо
                tempList[i + 1] = 1.
                # пристыковываем полученный набор к результирующему списку
                motherList.append(tempList)

    # список-заготовка из нулевых элементов
    zeroList: list = [x * 0 for x in range(vectorLength)]

    # результат, собственно
    result = []
    # первый элемент результата - список из нулевых элементов
    result.append(zeroList.copy())

    for j in range(startPosition, vectorLength):
        startStr = zeroList.copy()
        for m in range(startPosition, j + 1):
            # заполняем ведущими единицами
            startStr[m] = 1.

        # ^^^^ цикл, выдающий последовательно списки вида [1., 0., ..., 0.], [1., 1., ..., 0.], ..., [1., 1., ..., 1.]

        start = j
        stop = vectorLength

        result.append(startStr)
        oneTrip(start, stop, startStr, startPosition, result)
    return result

# print(onesAndZerosVariantsF(5, 0))

