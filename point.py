""" Модуль класса Точка: объект имеющий две координаты """
from torch import tensor as tnsr
from cmath import rect
import sys, traceback, inspect


class VectorComplex():
    """ Вектор. """
    def __init__(self, tensor_view: tnsr, origin=None):
        """

        :param tensor_view: Тензор вида [[0, 0]], Все параметры входного тензора сохраняются
        :param origin: координаты начала координат системы вектора в родительской системе координат
        """
        # super(VectorComplex, self).__init__()
        # тензорное представление вида [[0, 0]]
        self.__tensor = tensor_view
        # отдельно сохраняем данные тензора в родительском классе, ибо только они будут актуальными
        # self.__setPoint()
        # Есть система координат (А), в которой и лежит вектор
        # Сама система координат А, находится в рамках более глобальной системы Б.
        # Ниже указаны координаты начала координат системы А в рамках системы Б
        self.__origin: VectorComplex = origin
        # Если это поле равно None, то этот вектор находится в рамках самой глобальной системы координат.

    @classmethod
    def getInstance(cls, x=0., y=0., origin=None):
        """ Создать экземпляр класса. По умолчанию - нулевой вектор. """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # try:
        #     back_frame = inspect.currentframe().f_back.f_code.co_name
        #     if 0.086<=x<=0.088:
        #         raise Exception("(0.087; 0.996): {0}".format(back_frame))
        # except Exception:
        #     exc_type, exc_value, exc_traceback = sys.exc_info()
        #     traceback.print_tb(exc_traceback, file=sys.stdout)


        list = [[x, y]]
        tensor = tnsr(list, dtype=float)
        result = VectorComplex(tensor)
        result.__origin = origin
        return result

    @classmethod
    def getInstanceC(cls, complexNumber: complex, origin=None):
        """ Создать экземпляр класса на основе комплексного числа. """
        result = VectorComplex(tnsr([[complexNumber.real, complexNumber.imag]], dtype=float))
        result.__origin = origin
        return result

    def __getPair(self):
        """ Получить компоненты вектора в виде кортежа двух чисел с плавающей точкой. """
        # return self.__tensor[0][0], self.__tensor[0][1]
        # print(type(self.__tensor[0][0].item()), type(self.__tensor[0][1].item()))
        return self.__tensor[0][0].item(), self.__tensor[0][1].item()

    def __setPair(self, x:float, y: float):
        """ Установить/Изменить компоненты вектора """
        self.__tensor[0][0] = x
        self.__tensor[0][1] = y

    @property
    def tensor(self):
        """ Тензорный вид вектора """
        # self.__tensor[0][0] = self.__x
        # self.__tensor[0][1] = self.__y
        # return self.__tensor
        return tnsr([[self.__tensor[0][0].item(), self.__tensor[0][1].item()]], dtype=self.__tensor.dtype)

    @tensor.setter
    def tensor(self, tnsr: tensor):
        self.__tensor = tnsr
        # self.__setPoint()

    @property
    def decart(self):
        """
        :return: декартовы координаты точки
        """
        return self.__getPair()

    @decart.setter
    def decart(self, point: list):
        # if len(coord) != 2:
        #     raise Exception("List length mismatch")
        self.__setPair(point[0], point[1])

    @property
    def x(self):
        X, _ = self.__getPair()
        return X

    @property
    def y(self):
        _, Y = self.__getPair()
        return Y

    @property
    def cardanus(self):
        """
        :return: координаты точки в виде комплексного числа
        """
        x, y = self.__getPair()
        return complex(x, y)

    @cardanus.setter
    def cardanus(self, cmx: complex):
        """
        Установить координаты точки

        :param cmx: координаты в виде комплексного числа
        """
        self.__setPair(cmx.real, cmx.imag)

    @property
    def origin(self):
        """ Вектор начала координат дочерней системы в рамках родительской """
        return VectorComplex.getInstance(self.__origin.x, self.__origin.y)

    @origin.setter
    def origin(self, vector):
        """

        :param vector:
        :type vector: VectorComplex
        :return:
        """
        self.__origin = vector

    def rotate(self, angle: float):
        """
        Возвращает новый вектор, повёрнутый относительно изначального на заданный угол

        :param angle: угол поворота, радианы. Правая СК: против часовой стрелки > 0, Левая СК: по часовой > 0
        :return: новый, повёрнутый вектор
        :rtype VectorComplex:
        """
        # todo deprecated?
        return VectorComplex.getInstanceC(self.cardanus / rect(1., angle))

    def lazyCopy(self):
        """ Ленивая копия объекта: копируются только координаты """
        return VectorComplex.getInstance(self.x, self.y)

    # def abs(self):

    # @classmethod
    # def sub(cls, vector1, vector2):
    #     """ Вычитание векторов
    #
    #     :param vector1:
    #     :type vector1: VectorComplex
    #     :param vector2:
    #     :type vector2: VectorComplex
    #     """
    #     return VectorComplex(vector1.tensor - vector2.tensor)

    # @classmethod
    # def add(cls, vector1, vector2):
    #     """ Сложение векторов
    #
    #     :param vector1:
    #     :type vector1 VectorComplex
    #     :param vector2:
    #     :type vector2: VectorComplex
    #     """
    #     return VectorComplex(vector1.tensor + vector2.tensor)

    def __add__(self, other):
        """
        Сложение векторов.

        """
        return VectorComplex.getInstanceC(self.cardanus + other.cardanus)

    def __sub__(self, other):
        """
        Вычитание векторов.

        """
        return VectorComplex.getInstanceC(self.cardanus - other.cardanus)

    # def __mul__(self, other):
    #     """
    #     Умножение на число.
    #
    #     """
    #     if isinstance(other, complex):
    #         return VectorComplex.getInstanceC(self.cardanus * other)
    #
    #     try:
    #         # Вектор может умножаться только на число. К int можно привести любой объект, если он число, в т. ч. и float
    #         test = int(other)
    #     except TypeError("The 'other' argument is not a number-type"):
    #         # Бутафорская строка, чтобы что-то было в этом блоке
    #         other = other
    #     else:
    #         return VectorComplex.getInstanceC(self.cardanus * other)

    def __mul__(self, other):
        """
        Умножение на число.

        """
        if isinstance(other, (complex, int, float)):
            return VectorComplex.getInstanceC(self.cardanus * other)
        else:
            raise TypeError("The 'other' argument is not a number-type")

    def __rmul__(self, other):
        """
        Умножение на число. Обеспечение коммутативности.

        """
        return self.__mul__(other)

        # try:
        #     # Вектор может умножаться только на число.
        #     test = int(other)
        # except TypeError("The 'other' argument is not a number-type"):
        #     # Бутафорская строка, чтобы что-то было в этом блоке
        #     other = other
        # else:
        #     return VectorComplex.getInstanceC(self.cardanus * other)

    def __truediv__(self, other):
        """
        Деление на число.

        """
        if isinstance(other, complex):
            # Можно делить на комплексные число
            return VectorComplex.getInstanceC(self.cardanus / other)

        try:
            # Вектор может делиться только на число.
            test = int(other)
        except TypeError("The 'other' argument is not a number-type"):
            # Бутафорская строка, чтобы что-то было в этом блоке
            other = other
        else:
            return VectorComplex.getInstanceC(self.cardanus / other)

    def __neg__(self):
        """
        Унарный минус.

        """
        return VectorComplex.getInstance(-self.x, -self.y)

    def __str__(self):
        """ Строковое представление """
        return "x: {0:10.3f}, y: {1:10.3f}, abs: {2:10.3f}".format(self.x, self.y, abs(self.cardanus))

    def __abs__(self):
        """ Модуль вектора """
        # if self.x == float("inf") or self.y == float("inf"):
        #     return float("inf")
        return abs(self.cardanus)

