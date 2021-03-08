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
    heightJet = 0.5
    widthJet = 1


class Stage():
    """ Физические параметры ступени. """
    # Модель представляет из себя три массы, размещённые на разных высотах ракеты, что будет создавать необходимые
    # моменты вращения.

    # # Размеры в метрах
    # Sizes.heightCenterBlock = 30
    # Sizes.widthCenterBlock = 10

    # массы, в килограммах, по номерам снизу вверх
    # массы подобраны так, чтобы средняя масса (m1) была центром массс.

    # Масса в центре днища
    downMass = 2000
    # Масса в центре масс
    centerMass = 3000
    # Масса в центре верхней крышки
    topMass = 1000

    # координаты ключевых точек, относительно СЕРЕДИНЫ днища (что бы собирать ступень было легче?)
    # m0vector = VectorComplex(tensor([0, 0]))
    # m1vector = VectorComplex(tensor([0, Sizes.heightCenterBlock*1/3]))
    # m2vector = VectorComplex(tensor([0, Sizes.heightCenterBlock]))

    # Координаты точек с массой относительно центра масс
    centerMassVector = VectorComplex(tensor([0, 0]))
    topMassVector = VectorComplex(tensor([0., Sizes.heightCenterBlock * 2/3]))
    downMassVector = VectorComplex(tensor([0., - Sizes.heightCenterBlock * 1/3]))

    # плоскость посадочной опоры. Этой плоскостью ступень касается Земли.
    footVector = VectorComplex(tensor([0, - Sizes.heightCenterBlock * 1/3 - 1]))


