"""
Графические примитивы для канвы (метки, элементы ступени, стрелки и пр.)
"""
# Иерархия классов:
#
# AbstractPrimitive -> PoligonRectangleA
#   └-> AbstractOnCanvasMark
#           │-> CenterMassMark
#           └-> Arrow
#
from tkinter import Tk, Canvas, colorchooser, Toplevel, LAST
from point import VectorComplex
from decart import pointsListToNewCoordinateSystem
from abc import ABC, abstractmethod


class AbstractPrimitive(ABC):
    def __init__(self, canvas: Canvas, vectorComplex: tuple, centerPoint: VectorComplex):
        """
        Абстрактный класс-прародитель ВСЕХ примитивов на канве

        :param canvas: канва, на которой будет выводится данный примитив
        :param vectorComplex: список точек примитива.
        :param centerPoint: точка, во круг которой вращается примитив
        """
        # одно подчёркивание - protected, т. е. для экземпляра класса и его потомков
        self._canvas = canvas
        # Список точек типа VectorComplex, используется только для СОЗДАНИЯ примитива
        self._points = list(vectorComplex)
        # Идентификатор объекта на канве
        self._objOnCanvasId = None
        # Точка, вокруг которой осуществляется поворот многоугольника
        self._center = centerPoint

    @property
    def rotationCenter(self):
        return self._center

    @rotationCenter.setter
    def rotationCenter(self, point: VectorComplex):
        self._center = point

    @abstractmethod
    def move(self, vector: VectorComplex):
        """
        Перемещение примитива.

        :param vector: вектор смещения (т. к. tkinter использует для движения именно изменение координат)
        :return:
        """
        raise NotImplemented

    # @abstractmethod
    # def preliminaryMove(self, vector: VectorComplex, isCenterMassMove=False):
    #     """
    #     Предварительное смещение примитива (при сборке большого объекта) ДО первой отрисовки его на канве
    #
    #     :param vector: Вектор в СКК смещения от старой точки к новой
    #     :param isCenterMassMove: смещать центр масс, к которому привязан примитив
    #     :return:
    #     """
    #     raise NotImplemented

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
            # point.cardanus = point.cardanus + vector2d.cardanus
            point.cardanus = (point + vector2d).cardanus

        if isCenterMassMove:
            self._center.cardanus = (self._center + vector2d).cardanus

    # @abstractmethod
    # def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
    #     """
    #     Поворот примитива путём поворота направляющего вектора в сторону нового вектора
    #
    #     :param newAxisVector: направляющий вектор нового положения
    #     :param oldAxisVector: направляющий вектор старого положения
    #     :return:
    #     """
    #     raise NotImplemented

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

    @abstractmethod
    def createOnCanvas(self):
        """
        Создать примитив на канве
        """
        raise NotImplemented


class PoligonRectangleA(AbstractPrimitive):
    def __init__(self, canvas):
        """
        Создание объекта вызовом конструктора НЕ ПРОИЗВОДИТЬ!
        """
        super().__init__(canvas, tuple(), VectorComplex.getInstance())
        pass

    def create2points(self, topleft: VectorComplex, downright: VectorComplex, center: VectorComplex):
        """
        Создание прямоугольника по двум точкам. Примитива ещё не существует на канве.

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

    # def preliminaryMove(self, vector2d: VectorComplex, isCenterMassMove=False):
    #     """
    #     Метод предварительного смещения объекта в координатной системе канвы
    #
    #     :param vector2d: вектор смещения
    #     :param isCenterMassMove: сдвигать центр масс объекта вместе с остальными точками
    #     """
    #     #
    #     # Метод используется, например, при первоначальной отрисовки объекта. Т. е. объект сначала рисуется
    #     # в той позиции, где удобно задаваеть координаты его точек. Потом, испльзуется этот метод, для перемещения
    #     # примитива в нужное место, где он толжен быть примонтирован к основному объекту
    #     #
    #     for _, point in enumerate(self._points):
    #         point.cardanus = point.cardanus + vector2d.cardanus
    #
    #     if isCenterMassMove:
    #         self._center = self._center.cardanus + vector2d.cardanus

    def createOnCanvas(self):
        """
        Создать примитив на канве
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


class AbstractOnCanvasMark(AbstractPrimitive):
    """
    Класс независимых отметок, записей и пр. на канве
    """
    def __init__(self, canvas: Canvas, vectorComplex: tuple, centerPoint: VectorComplex):
        """
        :param canvas: канва
        :param vectorComplex: точки примитива, которые в дальнейшем разворачиваются в список для метода canvas.move
        :param centerPoint: точка крепления отметки на канве
        """
        super().__init__(canvas, vectorComplex, centerPoint)

    def move(self, pinPoint: VectorComplex):
        """
        Перемещение примитива к новой точке.

        :param pinPoint: новая точка, к которой цепляется примитив
        """
        if self._objOnCanvasId is not None:
            # вектор смещения
            moveVector = pinPoint - self._center
            # перемещаем по канве
            self._canvas.move(self._objOnCanvasId, moveVector.x, moveVector.y)
            # новая точка крепления
            self._center = pinPoint

    # def preliminaryMove(self, vector: VectorComplex, isCenterMassMove=False):
    #     # заглушаем эту функцию здесь, ибо дальнейшим наследникам она не нужна
    #     pass

    @abstractmethod
    def createOnCanvas(self):
        pass


class CenterMassMark(AbstractOnCanvasMark):
    """
    Отметка центра масс ступени
    """
    def __init__(self, canvas: Canvas, massCenter: VectorComplex, fill: str):
        """
        :param canvas: канва
        :param massCenter: вектор центра масс ступени
        :param fill: цвет заливки отметки
        """
        super().__init__(canvas,
                         (massCenter + VectorComplex.getInstance(-5, -5),
                          massCenter + VectorComplex.getInstance(5, 5)),
                         massCenter)
        self.__fill = fill

    # def preliminaryMove(self, vector: VectorComplex, isCenterMassMove=False):
    #     # для данного примитива метод не испльзуется.
    #     pass

    def createOnCanvas(self):
        """
        Создать примитив на канве
        """
        if self._objOnCanvasId is None:
            # Если примитив ещё нет на канве (то есть, он ещё ни разу не отрисовывался,
            # то можно его создавать и рисовать)

            # рисуем примитив на канве
            # так как примитив, фактически, создаётся на канве, то для конкретного примитива эта функция применяется
            # только один раз. Дальнейшие действия с примитивом делаются через его идентификатор,
            # который возвращает этот метод.
            self._objOnCanvasId = self._canvas.create_oval([self._points[0].x, self._points[0].y,
                                                            self._points[1].x, self._points[1].y], fill=self.__fill)


class Arrow(AbstractOnCanvasMark):
    """
    Отображение иллюстративной стрелки на канве
    """
    # def __init__(self, canvas: Canvas, *args, **kwargs):
    def __init__(self, canvas: Canvas, start: VectorComplex, finish: VectorComplex, width: float, color: str, pinPoint=VectorComplex.getInstance()):
        """
        :param canvas: канва
        :param start: начальная точка
        :param finish: конечная точка
        :param width: ширина линии
        :param color: цвет стрелки
        :param pinPoint: ось вращения
        """
        super().__init__(canvas, (start, finish), pinPoint)

        self.__width = width
        self.__color = color
        self.__pinPoint = pinPoint

    # def preliminaryMove(self, vector: VectorComplex, isCenterMassMove=False):
    #     # Для этого примитива функция не используется
    #     pass

    def createOnCanvas(self):
        """
        Создать примитив на канве
        """
        if self._objOnCanvasId is None:
            self._objOnCanvasId = self._canvas.create_line(self._points[0].x, self._points[0].y,
                                                            self._points[1].x, self._points[1].y,
                                                            width=self.__width, fill=self.__color, arrow=LAST)
    @property
    def arrow(self):
        """
        :return: начальная и конечная точка
        """
        arrowPoints = self._canvas.coords([self._objOnCanvasId])
        return (VectorComplex.getInstance(arrowPoints[0], arrowPoints[1]),
                VectorComplex.getInstance(arrowPoints[2], arrowPoints[3]))

    @arrow.setter
    def arrow(self, *args: VectorComplex):
        """
        :param args: два элемента типа VectorComlex: стартовая точка и конечная точка
        :return:
        """
        self._canvas.coords(self._objOnCanvasId, args[0].x, args[0].y, args[1].x, args[1].y)


class Text(AbstractOnCanvasMark):
    def __init__(self, canvas: Canvas, start: VectorComplex, text: str, key_point):
        """
        :param canvas: канва
        :param start: начальная точка
        :param finish: конечная точка
        :param width: ширина линии
        :param color: цвет стрелки
        """
        super().__init__(canvas, (start, start), start)

        self._key_point = key_point
        self._text = text
        # self.__width = width
        # self.__color = color

    def createOnCanvas(self):
        if self._objOnCanvasId is None:
            self._objOnCanvasId = self._canvas.create_text(self._points[0].x, self._points[0].y, text=self._text,
                                                           anchor=self._key_point, fill="black")
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value: str):
        if self._objOnCanvasId is not None:
            # меняем значение на канве
            self._canvas.itemconfig(self._objOnCanvasId, text=value)
            # сохраняем значение в объекте
            self._text = value