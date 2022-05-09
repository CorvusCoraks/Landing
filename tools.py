from point import VectorComplex
from math import fabs
# from stage import BigMap
from stage import Sizes, BigMap
from structures import RealWorldStageStatusN, StageControlCommands
# Разные утилиты

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
    minVector = VectorComplex.getInstance(0, 0)

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
            cls.minVector = VectorComplex(0, 0)
            return 0

        # подкрепление за удачную посадку
        if Finish.isOneTestSuccess(stageStatus, 0):
            successReinforcement = 100

        # подкрепление в процесс посадки
        # корректирующий подкрепление множитель
        mult = 0
        if abs(stageStatus.position) < abs(cls.minVector):
            # если достигли позиции ещё ближе, чем была самая близкая, то фиксируем данный радиус-вектор
            cls.minVector = stageStatus.position
            # собираем множитель, в зависимости от включённости двигателей
            mult =+ 0.5 if jets.topLeft else 0
            mult =+ 0.5 if jets.topRight else 0
            mult =+ 0.5 if jets.downLeft else 0
            mult =+ 0.5 if jets.downRight else 0
            mult =+ 2.0 if jets.main else 0
            # считаем подкрепление с учётом работавших двигателей
            landingReinforcement = 10 / mult

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

