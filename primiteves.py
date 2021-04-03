"""
Графические примитивы для канвы (метки, элементы ступени, стрелки и пр.)
"""
from tkinter import Tk, Canvas, colorchooser, Toplevel, LAST
from point import VectorComplex
from decart import fromOldToNewCoordSystem, pointsListToNewCoordinateSystem
from abc import ABC, abstractmethod


class AbstractPrimitive(ABC):
    def __init__(self, canvas: Canvas):
        """
        Абстрактный класс-прародитель ВСЕХ примитивов на канве

        :param canvas: канва, на которой будет выводится данный примитив
        """
        # одно подчёркивание - protected, т. е. для экземпляра класса и его потомков
        self._canvas = canvas
        # Список точек многоугольника типа VectorComplex
        self._points = []
        # Идентификатор объекта на канве
        self._objOnCanvasId = None
        # Точка, вокруг которой осуществляется поворот многоугольника
        self._center = VectorComplex.getInstance()

    @abstractmethod
    def move(self, vector: VectorComplex):
        """
        Перемещение примитива.

        :param vector: Вектор в СКК смещения от старой точки к новой
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def preliminaryMove(self, vector: VectorComplex, isCenterMassMove=False):
        """
        Предварительное смещение примитива (при сборке большого объекта)

        :param vector: Вектор в СКК смещения от старой точки к новой
        :param isCenterMassMove: смещать центр масс, к которому привязан примитив
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        """
        Поворот примитива путём поворота направляющего вектора в сторону нового вектора

        :param newAxisVector: направляющий вектор нового положения
        :param oldAxisVector: направляющий вектор старого положения
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def draw(self):
        """
        Рисовать примитив (если он не существует) на канве

        :return:
        """
        raise NotImplemented


# class PoligonRectangleA():
#     def __init__(self, canvas: Canvas):
#         """
#         :param canvas: канва, на которой будет выводится данный многоугольник
#         """
#         self.__canvas = canvas
#         # Список точек многоугольника типа VectorComplex
#         self.__points = []
#         # Идентификатор объекта на канве
#         self.__objOnCanvasId = None
#         # Точка, вокруг которой осуществляется поворот многоугольника
#         self.__center = VectorComplex.getInstance()
#         # вектор ориентации примитива. Изначально направлен по оси Y канвы
#         # self.__directionVector = Point(0., 1.)
#
#     def create2points(self, topleft: VectorComplex, downright: VectorComplex, center: VectorComplex):
#         """
#         Создание прямоугольника по двум точкам
#
#         :param topleft:
#         :param downright:
#         :param center: центр вращения примитива
#         :return:
#         """
#         self.__points = [topleft, VectorComplex.getInstance(downright.x, topleft.y),
#                          downright, VectorComplex.getInstance(topleft.x, downright.y)]
#         self.__center = center
#         return self
#
#     def move(self, vector2d: VectorComplex):
#         """
#         Двигать примитив.
#
#         :param vector2d: вектор, в направлении и на величину которого двигать примитив, т. е. смещение примитива
#         """
#         if self.__objOnCanvasId is not None:
#             # перемещаем по канве
#             # delta = vector2d
#             self.__canvas.move(self.__objOnCanvasId, vector2d.x, vector2d.y)
#             # пересчитываем положение центра вращения через смещение
#             # self.__center = VectorComplex.getInstanceC(self.__center.cardanus + vector2d.cardanus)
#             self.__center = self.__center + vector2d
#
#     def preliminaryMove(self, vector2d: VectorComplex, isCenterMassMove=False):
#         """
#         Метод предварительного смещения объекта в координатной системе канвы
#
#         :param vector2d: вектор смещения
#         :param isCenterMassMove: сдвигать центр масс объекта вместе с остальными точками
#         """
#         #
#         # Метод используется, например, при первоначальной отрисовки объекта. Т. е. объект сначала рисуется
#         # в той позиции, где удобно задаваеть координаты его точек. Потом, испльзуется этот метод, для перемещения
#         # примитива в нужное место, где он толжен быть примонтирован к основному объекту
#         #
#         for _, point in enumerate(self.__points):
#             point.cardanus = point.cardanus + vector2d.cardanus
#
#         if isCenterMassMove:
#             self.__center = self.__center.cardanus + vector2d.cardanus
#
#     def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
#         """
#         Поворот примитива.
#
#         :param newAxisVector: новый вектор оси ступени
#         :param oldAxisVector: старый вектор оси ступени
#         """
#         # получить координаты точек объекта в системе координат канвы
#         current = self.__canvas.coords(self.__objOnCanvasId)
#         points = []
#         # Преобразовать координаты точек в объекты типа VectorComplex в СК канвы
#         for i in range(len(self.__points)):
#             points.append(VectorComplex.getInstance(current[i * 2], current[i * 2 + 1]))
#         # Пересчитать координаты точек объектов из системы канвы в систему центра тяжести
#         # (координатные оси сонаправлены)
#         points = pointsListToNewCoordinateSystem(points, self.__center)
#         # Расчитать новые точки через поворот вокруг центра тяжести
#         # Угол поворота из старого положения
#         alpha_complex = VectorComplex.getInstanceC(newAxisVector.cardanus / oldAxisVector.cardanus)
#         # print("Угол поворота: {}, {}".format(phi, alpha_complex.cardanus))
#         # новые координаты точек объекта в системе координат относительно точки поворота
#         new_points = []
#         for value in points:
#             newPoint = VectorComplex.getInstanceC(value.cardanus * alpha_complex.cardanus)
#             new_points.append(newPoint)
#         # Новые точки пересчитать обратно в систему координат канвы
#         new_points = pointsListToNewCoordinateSystem(new_points, VectorComplex.getInstance(- self.__center.x, - self.__center.y))
#         # Обновить координаты точек в объекте (будет произведена автоматическое визуальное изменение)
#         canvas_points = []
#         for value in new_points:
#             canvas_points.append(value.x)
#             canvas_points.append(value.y)
#         self.__canvas.coords(self.__objOnCanvasId, canvas_points)
#
#     def draw(self):
#         """
#         Рисовать примитив (если он не существует) на канве
#         """
#         if self.__objOnCanvasId is None:
#             # Если примитив ещё нет на канве (то есть, он ещё ни разу не отрисовывался,
#             # то можно его создавать и рисовать)
#
#             # plain лист ключевых точек примитива (функция канвы только в таком виде воспринимает)
#             coord_list = [value.decart for value in self.__points]
#             # рисуем примитив на канве
#             # так как примитив, фактически, создаётся на канве, то для конкретного примитива эта функция применяется
#             # только один раз. Дальнейшие действия с примитивом делаются через его идентификатор,
#             # который возвращает этот метод.
#             self.__objOnCanvasId = self.__canvas.create_polygon(coord_list, fill="", outline="black")
#             # print(self.__canvas.coords(self.__objOnCanvasId))


class PoligonRectangleA(AbstractPrimitive):
    def __init__(self, canvas):
        super().__init__(canvas)
        pass

    # def __init__(self, canvas: Canvas):
    #     """
    #     :param canvas: канва, на которой будет выводится данный многоугольник
    #     """
    #     self.__canvas = canvas
    #     # Список точек многоугольника типа VectorComplex
    #     self.__points = []
    #     # Идентификатор объекта на канве
    #     self.__objOnCanvasId = None
    #     # Точка, вокруг которой осуществляется поворот многоугольника
    #     self.__center = VectorComplex.getInstance()
    #     # вектор ориентации примитива. Изначально направлен по оси Y канвы
    #     # self.__directionVector = Point(0., 1.)

    def create2points(self, topleft: VectorComplex, downright: VectorComplex, center: VectorComplex):
        """
        Создание прямоугольника по двум точкам

        :param topleft:
        :param downright:
        :param center: центр вращения примитива
        :return:
        """
        self._points = [topleft, VectorComplex.getInstance(downright.x, topleft.y),
                         downright, VectorComplex.getInstance(topleft.x, downright.y)]
        self._center = center
        return self

    def move(self, vector2d: VectorComplex):
        """
        Двигать примитив.

        :param vector2d: вектор, в направлении и на величину которого двигать примитив, т. е. смещение примитива
        """
        if self._objOnCanvasId is not None:
            # перемещаем по канве
            # delta = vector2d
            self._canvas.move(self._objOnCanvasId, vector2d.x, vector2d.y)
            # пересчитываем положение центра вращения через смещение
            # self.__center = VectorComplex.getInstanceC(self.__center.cardanus + vector2d.cardanus)
            self._center = self._center + vector2d

    def preliminaryMove(self, vector2d: VectorComplex, isCenterMassMove=False):
        """
        Метод предварительного смещения объекта в координатной системе канвы

        :param vector2d: вектор смещения
        :param isCenterMassMove: сдвигать центр масс объекта вместе с остальными точками
        """
        #
        # Метод используется, например, при первоначальной отрисовки объекта. Т. е. объект сначала рисуется
        # в той позиции, где удобно задаваеть координаты его точек. Потом, испльзуется этот метод, для перемещения
        # примитива в нужное место, где он толжен быть примонтирован к основному объекту
        #
        for _, point in enumerate(self._points):
            point.cardanus = point.cardanus + vector2d.cardanus

        if isCenterMassMove:
            self._center = self._center.cardanus + vector2d.cardanus

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        """
        Поворот примитива.

        :param newAxisVector: новый вектор оси ступени
        :param oldAxisVector: старый вектор оси ступени
        """
        # получить координаты точек объекта в системе координат канвы
        current = self._canvas.coords(self._objOnCanvasId)
        points = []
        # Преобразовать координаты точек в объекты типа VectorComplex в СК канвы
        for i in range(len(self._points)):
            points.append(VectorComplex.getInstance(current[i * 2], current[i * 2 + 1]))
        # Пересчитать координаты точек объектов из системы канвы в систему центра тяжести
        # (координатные оси сонаправлены)
        points = pointsListToNewCoordinateSystem(points, self._center)
        # Расчитать новые точки через поворот вокруг центра тяжести
        # Угол поворота из старого положения
        alpha_complex = VectorComplex.getInstanceC(newAxisVector.cardanus / oldAxisVector.cardanus)
        # print("Угол поворота: {}, {}".format(phi, alpha_complex.cardanus))
        # новые координаты точек объекта в системе координат относительно точки поворота
        new_points = []
        for value in points:
            newPoint = VectorComplex.getInstanceC(value.cardanus * alpha_complex.cardanus)
            new_points.append(newPoint)
        # Новые точки пересчитать обратно в систему координат канвы
        new_points = pointsListToNewCoordinateSystem(new_points, VectorComplex.getInstance(- self._center.x, - self._center.y))
        # Обновить координаты точек в объекте (будет произведена автоматическое визуальное изменение)
        canvas_points = []
        for value in new_points:
            canvas_points.append(value.x)
            canvas_points.append(value.y)
        self._canvas.coords(self._objOnCanvasId, canvas_points)

    def draw(self):
        """
        Рисовать примитив (если он не существует) на канве
        """
        if self._objOnCanvasId is None:
            # Если примитив ещё нет на канве (то есть, он ещё ни разу не отрисовывался,
            # то можно его создавать и рисовать)

            # plain лист ключевых точек примитива (функция канвы только в таком виде воспринимает)
            coord_list = [value.decart for value in self._points]
            # рисуем примитив на канве
            # так как примитив, фактически, создаётся на канве, то для конкретного примитива эта функция применяется
            # только один раз. Дальнейшие действия с примитивом делаются через его идентификатор,
            # который возвращает этот метод.
            self._objOnCanvasId = self._canvas.create_polygon(coord_list, fill="", outline="black")
            # print(self.__canvas.coords(self.__objOnCanvasId))


class CenterMassMark(AbstractPrimitive):
    def __init__(self, canvas: Canvas, *args, **kwargs):
        super().__init__(canvas)

        self.__topLeftX, self.__topLeftY, self.__downRightX, self.__downRightY = args
        self.__fill = kwargs.get('fill')

    def move(self, vector: VectorComplex):
        if self._objOnCanvasId is not None:
            # перемещаем по канве
            self._canvas.move(self._objOnCanvasId, vector.x, vector.y)
            # пересчитываем положение центра вращения через смещение
            self._center = self._center + vector

    def preliminaryMove(self, vector: VectorComplex, isCenterMassMove=False):
        """
        Метод предварительного смещения объекта в координатной системе канвы

        :param vector: вектор смещения
        :param isCenterMassMove: сдвигать центр масс объекта вместе с остальными точками
        """
        #
        # Метод используется, например, при первоначальной отрисовки объекта. Т. е. объект сначала рисуется
        # в той позиции, где удобно задаваеть координаты его точек. Потом, испльзуется этот метод, для перемещения
        # примитива в нужное место, где он толжен быть примонтирован к основному объекту
        #
        for _, point in enumerate(self._points):
            point.cardanus = point.cardanus + vector.cardanus

        if isCenterMassMove:
            self._center = self._center.cardanus + vector.cardanus

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        # вращать метку не нужно.
        pass

    def draw(self):
        """
        Рисовать примитив (если он не существует) на канве
        """
        if self._objOnCanvasId is None:
            # Если примитив ещё нет на канве (то есть, он ещё ни разу не отрисовывался,
            # то можно его создавать и рисовать)

            # plain лист ключевых точек примитива (функция канвы только в таком виде воспринимает)
            # coord_list = [value.decart for value in self._points]
            # рисуем примитив на канве
            # так как примитив, фактически, создаётся на канве, то для конкретного примитива эта функция применяется
            # только один раз. Дальнейшие действия с примитивом делаются через его идентификатор,
            # который возвращает этот метод.
            self._objOnCanvasId = self._canvas.create_oval([self.__topLeftX, self.__topLeftY, self.__downRightX, self.__downRightY], fill=self.__fill)
            # print(self.__canvas.coords(self.__objOnCanvasId))


class Arrow(AbstractPrimitive):
    # def __init__(self, canvas: Canvas, *args, **kwargs):
    def __init__(self, canvas: Canvas, start: VectorComplex, finish: VectorComplex, width: float, color:str):
        super().__init__(canvas)

        self.__canvas = canvas
        self.__start = start
        self.__finish = finish
        self.__width = width
        self.__color = color
        # self.__start, self.__finish, self.__width, self.__color = args
        # # self.__fill = kwargs.get('fill')
        # if self.__start is not isinstance(VectorComplex) and self.__finish is not isinstance(VectorComplex):

    def move(self, vector: VectorComplex):
        pass

    def preliminaryMove(self, vector: VectorComplex, isCenterMassMove=False):
        pass

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        pass

    def draw(self):
        if self._objOnCanvasId is None:
            self._objOnCanvasId = self.__canvas.create_line(self.__start.x, self.__start.y,
                                                            self.__finish.x, self.__finish.y,
                                                            width=self.__width, fill=self.__color, arrow=LAST)
        pass