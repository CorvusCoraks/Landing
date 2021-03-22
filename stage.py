""" Размеры и массы ступени. """
from point import VectorComplex
from torch import tensor


class Sizes():
    """ Геометрические параметы ступени и её составляющих """
    # Размеры центрального блока, размеры боковых реактивных рулей, размеры аэродинамических рулей
    # Эти данные нужны, в основном, чтобы рисовать на канве

    # Размеры в метрах

    # высота и ширина центрального блока
    heightCenterBlock = 30
    widthCenterBlock = 10
    # высота и ширина маневрового двигателя
    heightJet = 2
    widthJet = 5

    # расстояние до центра масс
    topMassDistance = heightCenterBlock * 2/3
    downMassDistance = heightCenterBlock * 1/3

    # Плечо приложения сил рулевых двигателей (от центра масс)
    topEnginesLeverage = heightCenterBlock * 2/3
    downEnginesLeverage = heightCenterBlock * 1/3


class Stage():
    """ Физические параметры ступени. """
    # Модель представляет из себя три массы, размещённые на разных высотах ракеты, что будет создавать необходимые
    # моменты вращения.

    # массы, в килограммах
    # массы подобраны так, чтобы средняя масса была центром массс.

    # Масса в центре днища
    downMass = 2000
    # Масса в центре масс
    centerMass = 3000
    # Масса в центре верхней крышки
    topMass = 1000

    # Координаты точек с массой относительно центра масс
    centerMassVector = VectorComplex(tensor([0, 0]))
    topMassVector = VectorComplex(tensor([0., Sizes.topMassDistance]))
    downMassVector = VectorComplex(tensor([0., - Sizes.downMassDistance]))

    # плоскость посадочной опоры. Этой плоскостью ступень касается Земли.
    footVector = VectorComplex(tensor([0, - Sizes.heightCenterBlock * 1/3 - 1]))

    # Момент инерции ступени
    InertionMoment = downMass * Sizes.downMassDistance ** 2 + topMass * Sizes.topMassDistance ** 2


class Engine():
    """
    Сила двигателей, Ньютоны
    """
    mainEngineForce = 100000
    steeringEngineForce = 10000


