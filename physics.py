from torch import Tensor
import torch

# модуль расчёта движения ступени согласно физическим законам
# Физическая модель ступени представляет из себя три жёстко связанные точки
# массой m1 (центр дна ракеты), m2 (средняя точка, центр масс), m3 (верх ступени)
# Движение ступени в рамках глобальных координат моделируется движением центра масс (точка m2)
# Ориентация ступени задаётся углом отклонения вертикального осевого вектора относительно вертикали глобальной
# системы координат.
# положение центра масс ступени и направляющий вектор передаются в модуль визуализации
# На остновании этих данных происходит отрисовка ступени на новом положении.

# def isLandingFinished():
#     """
#     Полёт завершён (посадка или взрыв - не известно)
#
#     :return:
#     """
#     # Координата центра тяжести
#     return False

def generateState():
    pass


class Vector():
    """
    Координаты точки.

    """
    def __init__(self, x=0., y=0., origin=None):
        # Координаты точки относительно начала координат
        self.__decart = torch.tensor([[x, y]])
        # Начало координат, относительно которого и заданы координаты данной точки.
        self.__origin: Vector = origin

    def origin(self, origin=None):
        """
        Точка начала координат.

        :param origin:
        :type origin: Vector
        :return:
        """
        if origin is None:
            return self.__origin
        else:
            self.__origin = origin

    def x(self, newX=None):
        """
        Получить или установить абциссу точки

        :param newX:
        :return:
        """
        if newX is None:
            return self.__decart[0][0].item()
        else:
            self.__decart[0][0] = newX

    def y(self, newY=None):
        """
        Получить или установить ординату точки

        :param newY:
        :return:
        """
        if newY is None:
            return self.__decart[0][1].item()
        else:
            self.__decart[0][1] = newY

    def tensor_view(self):
        """
        Получить тензорный вид вектора

        :return:
        """
        return self.__decart


class Rocket():
    """
    Класс ракеты / ступени
    """
    def __init__(self):
        # self.__baseVector: tensor = torch.zeros([1, 4])
        # координаты центра масс ракеты относительно точки посадки
        self.__coord: Vector
        # угол отклонения оси ступени от вертикали
        self.__psi = 0.

        # вектор скорости ракеты
        self.__v: Vector
        # вектор ускорения ракеты
        self.__a: Vector

        # Длина ракеты
        self.__l = 0.

        # координаты точек с массой (и сами массы) подобраны так, чтобы общий центр масс был в точке с ординатой 0
        # масса на верху ракеты
        self.__massTop = 0.
        # Ордината точки массы относительно центра масс
        self.__massTopCoord: Vector
        self.__massTopCoord = Vector(0, (2 / 3) * self.__l)
        # self.__massTopCoord[0][1] = (2 / 3) * self.__l
        # self.__massTopY = (2 / 3) * self.__l
        # масса в центре масс
        self.__massCenter = 0.
        # Ордината точки массы относительно центра масс
        self.__massCenterY = 0.
        # масса в нижней части ракеты
        self.__massDown = self.__massTop / 2
        # Ордината точки массы относительно центра масс
        self.__MassDownY = -(1 / 3) * self.__l

        # Импульс маневрового двигателя
        self.__pulseSteeringEngine = 0.
        # Импульст маршевого двигателя
        self.__pulsetumMainEngine = 0.

    def ganerateState(self):
        pass


class BigMap():
    def __init__(self, width: float, height: float):
        self.__width = width
        self.__height = height