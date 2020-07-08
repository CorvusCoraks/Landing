class Point():
    """
    Точка на координатной плоскости
    """
    def __init__(self, x=0, y=0):
        self.__x = x
        self.__y = y

    @property
    def decart(self):
        """
        :return: декартовы координаты точки
        """
        return self.__x, self.__y

    @decart.setter
    def decart(self, coord: list):
        # if len(coord) != 2:
        #     raise Exception("List length mismatch")

        self.__x = coord[0]
        self.__y = coord[1]

    @property
    def cardanus(self):
        """
        :return: координаты точки в виде комплексного числа
        """
        return complex(self.__x, self.__y)

    @cardanus.setter
    def cardanus(self, cmx: complex):
        """
        Установить координаты точки

        :param cmx: координаты в виде комплексного числа
        """
        self.__x = cmx.real
        self.__y = cmx.imag

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x: float):
        self.__x = x

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y: float):
        self.__y = y


class Transform():
    """
    Изменение положения объекта.
    """
    def __init__(self, vector2d: Point, orientation2d: Point, text: str):
        """

        :param vector2d: вектор перемещения объекта в системе координат канвы
        :param orientation2d: вектор ориентации объекта в системе координат канвы
        :param text: строка допоплнительной информации
        """
        self.vector2d = vector2d
        self.orientation2d = orientation2d
        self.text = text