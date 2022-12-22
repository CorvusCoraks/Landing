""" Модуль класса Точка: объект имеющий две координаты """
# from torch import tensor as torch_tensor
from cmath import rect
from typing import Union, Tuple
# from torch import float as torch_float

# Тип, означающий число
NumberType = Union[complex, int, float]


class VectorComplex:
    """ Вектор. Объект данного класса создавать только методами *get_instance* или *get_instance_c* """

    # ключ, необходимый, для контроля того, что объекты данного класса создаются только разрешёнными методами
    # Значение создаётся при инициализации модуля
    # https://stackoverflow.com/questions/8212053/private-constructor-in-python
    __create_key = object()

    def __init__(self, create_key: object, x: float, y: float, origin=None):
        """
        Объект данного класса создавать только методами *get_instance* или *get_instance_c*

        :param create_key: ключ для контроля того, что объекты данного класса создаются только разрешёнными методами
        :param tensor_view: Тензор вида [[0, 0]], Все параметры входного тензора сохраняются
        :param origin: координаты начала координат системы вектора в родительской системе координат
        """
        # Если ключ в вызывающем методе не совпадает с установленным во время инициализации, то инициируется ошибка.
        # И правильно. Объекты данного класса создаются только разрешёнными методами.
        assert(create_key == VectorComplex.__create_key), \
            "VectorComplex objects must be created using getInstanse or get_instance_c method."

        self._x = x
        self._y = y

        # тензорное представление вида [[0, 0]]
        # self.__tensor = tensor_view
        # отдельно сохраняем данные тензора в родительском классе, ибо только они будут актуальными
        # self.__setPoint()
        # Есть система координат (А), в которой и лежит вектор
        # Сама система координат А, находится в рамках более глобальной системы Б.
        # Ниже указаны координаты начала координат системы А в рамках системы Б
        # todo этот атрибут, как мне кажется, нигде не используется. Удалить?
        self.__origin: VectorComplex = origin
        # Если это поле равно None, то этот вектор находится в рамках самой глобальной системы координат.

    @classmethod
    def get_instance(cls, x=0., y=0., origin=None) -> 'VectorComplex':
        """ Создать экземпляр класса. По умолчанию - нулевой вектор.

        :param x: абцисса конечной точки вектора.
        :param y: ордината конечной точки вектора.
        """

        # lst = [[x, y]]
        # tensor = torch_tensor(lst, dtype=torch_float)
        # result = VectorComplex(VectorComplex.__create_key, tensor)
        # self._x = x
        # self._y = y
        # result.__origin = origin
        return VectorComplex(VectorComplex.__create_key, x, y, origin)

    @classmethod
    def get_instance_c(cls, complex_number: complex, origin=None) -> 'VectorComplex':
        """ Создать экземпляр класса на основе комплексного числа.

        :param complex_number: комплексное число, представляющее компоненты вектора (real - x, img - y)
        """
        # result = VectorComplex(VectorComplex.__create_key, torch_tensor([[complex_number.real, complex_number.imag]],
        #                                                                 dtype=torch_float))
        # result.__origin = origin
        return VectorComplex(VectorComplex.__create_key, complex_number.real, complex_number.imag, origin)

    # def __get_pair(self) -> Tuple[float, float]:
    #     """ Получить компоненты вектора в виде кортежа двух чисел с плавающей точкой. """
    #     # return self.__tensor[0][0], self.__tensor[0][1]
    #     # print(type(self.__tensor[0][0].item()), type(self.__tensor[0][1].item()))
    #     # return self.__tensor[0][0].item(), self.__tensor[0][1].item()
    #     return self._x, self._y
    #
    # def __set_pair(self, x: float, y: float):
    #     """ Установить/Изменить компоненты вектора
    #
    #     :param x: абцисса конечной точки вектора.
    #     :param y: ордината конечной точки вектора.
    #     """
    #     # self.__tensor[0][0] = x
    #     # self.__tensor[0][1] = y
    #     self._x = x
    #     self._y = y

    # @property
    # def tensor(self) -> torch_tensor:
    #     """ Тензорный вид вектора """
    #     # self.__tensor[0][0] = self.__x
    #     # self.__tensor[0][1] = self.__y
    #     # return self.__tensor
    #     return torch_tensor([[self.__tensor[0][0].item(), self.__tensor[0][1].item()]], dtype=self.__tensor.dtype)
    #
    # @tensor.setter
    # def tensor(self, tnsr: torch_tensor):
    #     self.__tensor = tnsr
    #     # self.__setPoint()

    @property
    def decart(self) -> Tuple[float, float]:
        """
        Получить координаты конца вектора.

        :return: декартовы координаты точки
        """
        # return self.__get_pair()
        return self._x, self._y

    @decart.setter
    def decart(self, point: Tuple[float, float]):
        """ Установить координаты конца вектора. """
        if len(point) != 2:
            raise Exception("Argument 'point' length ({0}) mismatch".format(len(point)))
        # self.__set_pair(point[0], point[1])
        self._x, self._y = point

    @property
    def x(self) -> float:
        """ Абцисса конца вектора. """
        # x, _ = self.__get_pair()
        return self._x

    @property
    def y(self) -> float:
        """ Ордината конца вектора. """
        # _, y = self.__get_pair()
        return self._y

    @property
    def cardanus(self) -> complex:
        """
        :return: координаты точки в виде комплексного числа
        """
        # x, y = self.__get_pair()
        # return complex(x, y)
        return complex(self._x, self._y)

    @cardanus.setter
    def cardanus(self, cmx: complex):
        """
        Установить координаты точки

        :param cmx: координаты в виде комплексного числа
        """
        # self.__set_pair(cmx.real, cmx.imag)
        self._x, self._y = cmx.real, cmx.imag

    @property
    def origin(self):
        """ Вектор начала координат дочерней системы в рамках родительской """
        # thisClass = self.__class__
        # todo убрать метод и атрибут?
        return VectorComplex.get_instance(self.__origin.x, self.__origin.y)

    @origin.setter
    def origin(self, vector):
        """

        :param vector:
        :type vector: VectorComplex
        :return:
        """
        # todo убрать метод и атрибут?
        self.__origin = vector

    def rotate(self, angle: float) -> 'VectorComplex':
        """
        Возвращает новый вектор, повёрнутый относительно изначального на заданный угол

        :param angle: угол поворота, радианы. Правая СК: против часовой стрелки > 0, Левая СК: по часовой > 0
        :return: новый, повёрнутый вектор
        """
        # todo deprecated?
        return VectorComplex.get_instance_c(self.cardanus / rect(1., angle))

    def lazy_copy(self) -> 'VectorComplex':
        """ Ленивая копия объекта: копируются только координаты """
        # todo заменить на deepcopy?
        return VectorComplex.get_instance(self.x, self.y)

    def __add__(self, other: 'VectorComplex') -> 'VectorComplex':
        """
        Сложение векторов.

        """
        return VectorComplex.get_instance_c(self.cardanus + other.cardanus)

    def __sub__(self, other: 'VectorComplex') -> 'VectorComplex':
        """
        Вычитание векторов.

        """
        return VectorComplex.get_instance_c(self.cardanus - other.cardanus)

    def __mul__(self, other: NumberType) -> 'VectorComplex':
        """
        Умножение на число.

        """
        if isinstance(other, (complex, int, float)):
            return VectorComplex.get_instance_c(self.cardanus * other)
        else:
            raise TypeError("The 'other' argument is not a number-type")

    def __rmul__(self, other: NumberType) -> 'VectorComplex':
        """
        Умножение на число. Обеспечение коммутативности.

        """
        return self.__mul__(other)

    def __truediv__(self, other: NumberType) -> 'VectorComplex':
        """
        Деление на число.

        """
        if isinstance(other, complex):
            # Можно делить на комплексные число
            return VectorComplex.get_instance_c(self.cardanus / other)
        try:
            # Вектор может делиться только на число.
            test = int(other)
        except TypeError("The 'other' argument is not a number-type"):
            # Бутафорская строка, чтобы что-то было в этом блоке
            other = other
        else:
            # если получилось привести other к int, значит это либо float, либо int и можно на него делить
            return VectorComplex.get_instance_c(self.cardanus / other)

    def __neg__(self) -> 'VectorComplex':
        """
        Унарный минус.

        """
        return VectorComplex.get_instance(-self.x, -self.y)

    def __str__(self) -> str:
        """ Строковое представление """
        return "x: {0:10.3f}, y: {1:10.3f}, abs: {2:10.3f}".format(self.x, self.y, abs(self.cardanus))

    def __abs__(self) -> float:
        """ Модуль вектора """
        return abs(self.cardanus)
