""" Возможно, модуль устарел. """
from torch import tensor, mm, add, addmv, unsqueeze, squeeze
from math import sin, cos
from point import VectorComplex
from cmath import rect


def from_local_to_global(point_in_local: list, local_origin_in_global: list, alpha_ox: float, all_right=True):
    """
    Метод преобразования координат из локальных в глобальные. Устарело? complexChangeSystemCoordinatesUniversal

    :param alpha_ox: угол (со знаком, в радианах) оси OX' ступени относительно оси OX глобальной
    :param point_in_local: координаты точки в системе координат связанной со ступенью. Список вида [x, y]
    :param local_origin_in_global: координаты центра масс ступени в глобальной системе координат. Список вида [x, y]
    :param all_right: если переход из правой в правую (из левой в левую), то True, иначе - False
    :return: список вида [x, y]
    :rtype list:
    """
    if all_right:
        # матрица перехода из правой системы координат в правую
        transitionMatrix = tensor([[cos(alpha_ox), -sin(alpha_ox)], [sin(alpha_ox), cos(alpha_ox)]], dtype=float)
    else:
        transitionMatrix = tensor([[cos(alpha_ox), sin(alpha_ox)], [sin(alpha_ox), -cos(alpha_ox)]], dtype=float)
    source = tensor(point_in_local, dtype=float)
    local = tensor(local_origin_in_global, dtype=float)
    # global_position2 = mm(transitionMatrix, sourcePoint)
    # global_position2 = add(global_position2, massCenter)
    global_position = addmv(local, transitionMatrix, source)
    return global_position.tolist()


def from_local_to_global_points(points_in_local: list, local_origin_in_global: list, alpha_ox: float, all_right=True):
    """
    Метод преобразования координат списка точек из локальных в глобальные. Устарело? complexChangeSystemCoordinatesUniversal

    :param alpha_ox: угол (со знаком, в радианах) оси OX' локальной системы относительно оси OX глобальной
    :param points_in_local: координаты точек в локальной системе координат. Список вида [[x, y], [x, y]]
    :param local_origin_in_global: координаты начала локальной системы координат в глобальной системе координат. Список вида [x, y]
    :param all_right: если переход из правой в правую (из левой в левую), то True, иначе - False
    :return: список вида [[x, y], [x, y]]
    :rtype list:
    """
    if all_right:
        # матрица перехода из правой системы координат в правую
        transitionMatrix = tensor([[cos(alpha_ox), -sin(alpha_ox)], [sin(alpha_ox), cos(alpha_ox)]], dtype=float)
    else:
        transitionMatrix = tensor([[cos(alpha_ox), sin(alpha_ox)], [sin(alpha_ox), -cos(alpha_ox)]], dtype=float)

    sourse_tensors = [tensor(value, dtype=float) for value in points_in_local]
    # source = tensor(point_in_local, dtype=float)
    local = tensor(local_origin_in_global, dtype=float)
    # global_position2 = mm(transitionMatrix, sourcePoint)
    # global_position2 = add(global_position2, massCenter)
    global_position = [addmv(local, transitionMatrix, value).tolist() for value in sourse_tensors]
    # global_position = addmv(local, transitionMatrix, source)
    return global_position


def fromOldToNewCoordSystem(oldSystemVectors: list, oldOriginInNewCoordSystem: VectorComplex,
                            alpha_ox: float, isRightToRight=True):
    """
    Метод преобразования координат списка векторов из одной системы координат в другую. Устарело? complexChangeSystemCoordinatesUniversal

    :param alpha_ox: угол (со знаком, в радианах) поворота оси OX старой СК в сторону новой оси OX в кратчайшем напр.
    :param oldSystemVectors: координаты точек в старой системе координат. Список вида [VectorComplex, VectorComplex]
    :param oldOriginInNewCoordSystem: координаты типа VectorComplex начала старой системы координат в новой системе координат
    :param isRightToRight: если переход из правой в правую (из левой в левую), то True, иначе - False
    :return: список вида [VectorComplex, VectorComplex]
    :rtype list:
    """
    # Угол по часовой стрелке - отрицательный, против часовой стрелки - положительный
    #
    # Формулы перехода из одной системы координат в другую обычно слева имеют известные (x, y) старой системы коодинат,
    # а справа (вместе с матрицей перехода) неизвестные (x', y') новой системы координат,
    # в которую и осуществляется переход.
    #
    # Переворачиваем ситуацию. Вид формул остаётся прежним, но переход считаем в обратную сторону: из (x', y') в (x, y).
    # Таким образом (x, y) становятся неизвестными, которые мы и получаем прямым решением выражений правой части,
    # там, где матрица перехода, и где находятся ставшие известными (x', y').
    #
    # Смещение в фомулах: смещение начала координат системы Y'O'X' в системе координат YOX
    # (то есть, смещение начала координат старой системы относительно начала координат новой системы.
    #
    # Но угол поворота остаётся прежним: угол поворота оси OX в сторону O'X'. Т. е. это угол поворота системы координат
    # левой части выражений в сторону системы координат правой части выражений.
    #
    # Мистические объяснения.
    #
    # Правая система координат
    # Угол - угол поворота от старой ОХ к новой ОХ со стандартный знаком
    # Начавло координат новой СК в координатах старой СК
    # Левая система координат
    # При нулевом угле всё работает отлично.
    # Остальные углы по обратному принципу: по часовой стрелке - положительный, против часовой стрелки - отрицательный
    #
    if isRightToRight:
        # матрица перехода из правой системы координат в правую
        transitionMatrix = tensor([[cos(alpha_ox), -sin(alpha_ox)], [sin(alpha_ox), cos(alpha_ox)]], dtype=float)
    else:
        # Мистическое, но необходимое изменение знака угла. Иначе, нет прехода из левой в правую, из правой
        # в левую систему координат. Формулы этого не требуют, а практика да. Мистика.
        alpha_ox = -alpha_ox
        # Матрица перехода из правой в левую (из левой в правую) СК
        transitionMatrix = tensor([[cos(alpha_ox), sin(alpha_ox)], [sin(alpha_ox), -cos(alpha_ox)]], dtype=float)

    newSystemVectors = []
    # Преобразовать начало координат старой системы в одномерный тензор
    oldOriginTensor = squeeze(oldOriginInNewCoordSystem.tensor)
    # oldOriginTensor.dtype = float
    # Перебираем в цикле координаты точек
    for value in oldSystemVectors:
        # убрать внешнее измерение, превратив тензор в одномерный
        mutable = squeeze(value.tensor)
        # mutable.dtype = float
        # преобразовать одномерный вектор в другую систему координат
        mutable = addmv(oldOriginTensor, transitionMatrix, mutable)
        # добавть внешнее измерение, превратив тензор в двумерный
        mutable = unsqueeze(mutable, 0)
        # добавить результат в лист
        newSystemVectors.append(VectorComplex(mutable))
    return newSystemVectors


def complexChangeSystemCoordinatesUniversal(vectorInOldCoordinates: VectorComplex,
                                            originMoveVector: VectorComplex,
                                            angleRadians: float, isDiffType=False):
    """ Изменение системы координат через комплексные числа. Возможна смена типа системы координат.

    :param vectorInOldCoordinates: вектор в старой системе координат
    :param originMoveVector: вектор начала координат новой координатной системы внутри старой
    :param angleRadians: угол, на который повёрнута новая система координат относительно старой, >0 против часовой
    :param isDiffType: если из левой в левую или из правой в правую = False. Иначе = True
    """
    # Правая система координат: абцисса вправо, ордината вверх. В частности, система координат "обычная"
    # Левая система координат: абцисса вправо, ордината вниз. В частности, система координат канвы Tkinter
    #
    # Если изменение идёт с правой на левую, то положительный поворот по часовой стрелке
    # Если изменение идёт с левой на левую, то положительный поворот по часовой стрелке
    # Если изменение идёт с левой на правую, то положительный поворот против часовой стрелки
    # Если изменение идёт с правой на правую, то положительный поворот против часовой стрелки
    # Это всё проверено опытным путём....
    def complexMove(originMoveVector: VectorComplex, vectorInOldCoordinates: VectorComplex):
        """ Смещение начала координат от старой СК к новой """
        # result = VectorComplex.getInstanceC(- originMoveVector.cardanus + vectorInOldCoordinates.cardanus)
        result = -originMoveVector + vectorInOldCoordinates

        if isDiffType:
            # если при мереходе меняется тип системы координат, то меняем знак у ординаты смещённого начала координат
            result.decart = [result.x, - result.y]

        return result

    newShiftVector = complexMove(originMoveVector, vectorInOldCoordinates)

    # print(rect(1., angleRadians))
    # return VectorComplex.getInstanceC(newShiftVector.cardanus / rect(1., angleRadians))
    return newShiftVector / rect(1., angleRadians)


def pointsListToNewCoordinateSystem(pointsListInOldSystem: list, newSystemOrigin: VectorComplex, angleRadians=0., isDiffType=False):
    """
    Перевод списка точек (векторов) из одной системы координат в другую.

    :param pointsListInOldSystem: координаты точек в старой системе координат. Список вида [VectorComplex, VectorComplex]
    :param newSystemOrigin: координаты типа VectorComplex начала новой системы координат в старой
    :param angleRadians: угол, на который повёрнута новая система координат относительно старой, >0 против часовой
    :param isDiffType: если из левой в левую или из правой в правую = False. Иначе = True
    :return:
    :rtype list:
    """
    result = []
    for _, vector in enumerate(pointsListInOldSystem):
        result.append(complexChangeSystemCoordinatesUniversal(vector, newSystemOrigin, angleRadians, isDiffType))
    return result
