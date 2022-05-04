""" Физические размеры и массы ступени. """
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

    # максимальный габаритный размер ракеты (для вписывания в окно)
    overallDimension = heightCenterBlock

    # высота и ширина маневрового двигателя
    heightJet = 2
    widthJet = 5

    # высота и ширина маршевого двигателя
    heightMainJet = 10
    widthMainJet = 4

    # расстояние до центра масс
    topMassDistance = heightCenterBlock * 2/3
    downMassDistance = heightCenterBlock * 1/3

    # Плечо приложения сил рулевых двигателей (от центра масс)
    topEnginesLeverage = heightCenterBlock * 2/3
    downEnginesLeverage = heightCenterBlock * 1/3

    # расстояние от центра масс до плоскости опоры (в реальности, положение центра масс является функцией времени)
    massCenterFromLandingPlaneDistance = 2 + downMassDistance

class Stage():
    """ Физические параметры ступени. """
    # Модель представляет из себя три массы, размещённые на разных высотах ракеты, что будет создавать необходимые
    # моменты вращения.

    # массы, в килограммах
    # массы подобраны так, чтобы средняя масса была центром массс.
    # Стартовая масса РН Протон - 705 тонн (для справки и ориентировки)
    # Посадочная масса - ~10% от стартовой массы, т. е. ~70 тонн
    # Для целей опыта произвольно используем 60 тонн.

    # Масса в центре днища
    downMass = 20000
    # Масса в центре масс
    centerMass = 30000
    # Масса в центре верхней крышки
    topMass = 10000

    # Координаты точек с массой относительно центра масс
    centerMassVector = VectorComplex(tensor([0, 0]))
    topMassVector = VectorComplex(tensor([0., Sizes.topMassDistance]))
    downMassVector = VectorComplex(tensor([0., - Sizes.downMassDistance]))

    # плоскость посадочной опоры. Этой плоскостью ступень касается Земли.
    footVector = VectorComplex(0., -Sizes.massCenterFromLandingPlaneDistance)

    # Момент инерции ступени
    InertionMoment = downMass * Sizes.downMassDistance ** 2 + topMass * Sizes.topMassDistance ** 2

    # @classmethod
    # def downMass(cls):
    #     return 20000
    #
    # @classmethod
    # def centerMass(cls):
    #     return 30000
    #
    # @classmethod
    # def topMass(cls):
    #     return 10000


class Engine():
    """
    Сила двигателей, Ньютоны
    """
    mainEngineForce = 100000
    steeringEngineForce = 10000

class BigMap:
    """ Класс испытательного полигона """
    # # Ширина полигона в метрах
    # width = 300000
    # # Высота полигона в метрах
    # height = 100000
    # Временный размер на отладку
    # Ширина полигона в метрах
    width = 100
    # Высота полигона в метрах
    height = 500
    # Координаты начала координат СКИП в системе координат канвы (СКК) в масштабе 1:1
    # todo логически не верно, это же карта полигона. Убрать.
    testPoligonOriginInCCS = VectorComplex.getInstance(width / 2, height * 0.95)
    # Координаты начала координат СКК в СКИП в масштабе 1:1
    canvasOriginInPoligonCoordinates = VectorComplex.getInstance(- width / 2, height * 0.95)
    # Координаты точки приземления в СКИП
    landingPointInPoligonCoordinates = VectorComplex.getInstance()
    # Координаты стартовой точки в СКИП
    startPointInPoligonCoordinates = VectorComplex.getInstance(0., height * 0.9)
    # Координаты центра тяжести ступени (координаты начала координат СКС в СКИП в масштабе 1:1)
    # Движущаяся система координат.
    stageViewOriginInPoligonCoordinates = VectorComplex.getInstance()


