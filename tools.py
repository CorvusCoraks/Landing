from point import VectorComplex
from math import fabs
from physics import BigMap
from stage import Sizes
# Разные утилиты


class Reinforcement():
    """
    Класс подкрепления.

    """
    # Подкрепление > 0 только в случае успешной посадки.
    # Подкрепление = 1 только в случае посадки в центр площадки. Чем ближе к центру, тем больше подкрепление.
    # Во всех остальных случаях - 0
    def __init__(self):
        pass

    # метод удалить на фиг. Использовать метод из класса Finish
    def isLandingFinished(self, coord: VectorComplex, yMassCenter: float):
        """
        Считается, что процесс посадки (испытание) завершён. Результат  процесса - неизвестен

        :param coord: координаты центра масс ступени в мировой системе координат
        :param yMassCenter: высота центра масс ступени над плоскостю посадочных опор
        :return: ступень коснулась земной поверхности?
        """
        # Процесс может завершиться поразному: успешная посадка, неудачная посадка, ступень улетела за границы
        # контролируемого пространства. Все эти варианты надо учесть.
        if coord.y <= yMassCenter + self.__yEpsilon:
            # ступень коснулась земил
            result = True
        else:
            result = False
        return result

    def getReinforcement(self, coord: VectorComplex, yMassCenter: float):
        if self.isLandingFinished(coord, yMassCenter):
            # Проверка на высоту
            # Проверка на точность попадания в круг
            # Проверка на конечную скорость
            # Проверка на конечное ускорение
            # Проверка на ориентацию
            # Проверка на конечную угловую скорость
            # Проверка на конечное угловое ускорение
            pass
        return 0


class Finish():
    """
    Класс завершения единичного испытания
    """
    # Необходим для того, чтобы единичное испытание не длилось чрезмерное неразумное время
    def __init__(self):
        # Ширина тестового полигона. Точка посадки находится посередине
        # self.__testPoligonWidth = BigMap.width
        # Высота тестового полигона. Имеет смысл задавать её от высоты начальной точки движения до высоты точки посадки
        # self.__testPoligonHeight = BigMap.height
        # Допустимое отклонение при выявлении факта посадки (метров)
        self.__yEpsilon = 0.01
        # Высота выключения двигателей (по высоте центра масс)
        self.__legRelativeY = Sizes.massCenterFromLandingPlaneDistance

    def isOneTestFinished(self, coord: VectorComplex):
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
            or coord.y < self.__legRelativeY - self.__yEpsilon:
            # or (-self.__yEpsilon < coord.y + self.__legRelativeY < self.__yEpsilon) \
            # or coord.y < self.__legRelativeY - self.__yEpsilon:
            # Если ступень вылетела за пределы испытательного полигона:
            # - ступень вылетела за левую/правую границу полигона
            # - вылетела за верхнюю границу полигона
            # - вылетела за нижнюю границу полигона
            # испытание завершено
            return True

        return False