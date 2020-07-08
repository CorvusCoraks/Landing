from torch import tensor, mm, add, addmv
from math import sin, cos


def from_local_to_global(point_in_local: list, local_origin_in_global: list, alpha_ox: float, all_right=True):
    """
    Метод преобразования координат из локальных в глобальные

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
    Метод преобразования координат списка точек из локальных в глобальные

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