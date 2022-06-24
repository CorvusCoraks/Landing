""" Возможно, модуль устарел. """
from point import VectorComplex
from cmath import rect
from typing import List


def complexChangeSystemCoordinatesUniversal(vectorInOldCoordinates: VectorComplex,
                                            originMoveVector: VectorComplex,
                                            angleRadians: float, isDiffType=False) -> VectorComplex:
    """ Изменение системы координат через комплексные числа. Возможна смена типа системы координат.

    :param vectorInOldCoordinates: вектор в старой системе координат
    :param originMoveVector: вектор начала координат новой координатной системы внутри старой
    :param angleRadians: угол, на который повёрнута новая система координат относительно старой
    :param isDiffType: если из левой в левую или из правой в правую = False. Иначе = True
    """
    # Правая система координат: абцисса вправо, ордината вверх. В частности, система координат "обычная"
    # Левая система координат: абцисса вправо, ордината вниз. В частности, система координат канвы Tkinter
    #
    # ВАЖНО!
    # Если изменение идёт с правой на левую, то положительный поворот по часовой стрелке
    # Если изменение идёт с левой на левую, то положительный поворот по часовой стрелке
    # Если изменение идёт с левой на правую, то положительный поворот против часовой стрелки
    # Если изменение идёт с правой на правую, то положительный поворот против часовой стрелки
    # Это всё проверено опытным путём....
    def complexMove(originMoveVector: VectorComplex, vectorInOldCoordinates: VectorComplex) -> VectorComplex:
        """ Смещение начала координат от старой СК к новой """
        result = -originMoveVector + vectorInOldCoordinates

        if isDiffType:
            # если при мереходе меняется тип системы координат, то меняем знак у ординаты смещённого начала координат
            result.decart = (result.x, - result.y)

        return result

    newShiftVector = complexMove(originMoveVector, vectorInOldCoordinates)

    # поворот вектора и на выход
    return newShiftVector / rect(1., angleRadians)


def pointsListToNewCoordinateSystem(pointsListInOldSystem: List[VectorComplex], newSystemOrigin: VectorComplex,
                                    angleRadians=0., isDiffType=False) -> List[VectorComplex]:
    """
    Перевод списка точек (векторов) из одной системы координат в другую.

    :param pointsListInOldSystem: координаты точек в старой системе координат. Список вида [VectorComplex, VectorComplex]
    :param newSystemOrigin: координаты типа VectorComplex начала новой системы координат в старой
    :param angleRadians: угол, на который повёрнута новая система координат относительно старой
    :param isDiffType: если из левой в левую или из правой в правую = False. Иначе = True
    :return: список точек в новой системе координат
    """
    result: List[VectorComplex] = []
    for _, vector in enumerate(pointsListInOldSystem):
        result.append(complexChangeSystemCoordinatesUniversal(vector, newSystemOrigin, angleRadians, isDiffType))
    return result
