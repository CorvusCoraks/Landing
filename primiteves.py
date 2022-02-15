"""
Графические примитивы для канвы (метки, элементы ступени, стрелки и пр.)
"""
# Иерархия классов:
#
# AbstractPrimitive -> PoligonRectangleA
#   └-> AbstractOnCanvasMark
#           │-> CenterMassMark
#           └-> Arrow
#           └-> Text
#           └-> PsevdoArcArrow
from tkinter import Tk, Canvas, colorchooser, Toplevel, LAST, ARC, N
from point import VectorComplex
from decart import pointsListToNewCoordinateSystem
from abc import ABC, abstractmethod
from cmath import rect, pi
from math import radians

class AbstractPrimitive(ABC):
    def __init__(self, canvas: Canvas, vectorComplex: tuple, centerPoint: VectorComplex):
        """
        Абстрактный класс-прародитель ВСЕХ примитивов на канве

        :param canvas: канва, на которой будет выводится данный примитив
        :param vectorComplex: список точек примитива для его первоначальной отрисовки
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
        # todo зачем всё так сложно? Может использовать метод canvas.move?
        for _, point in enumerate(self._points):
            # point.cardanus = point.cardanus + vector2d.cardanus
            point.cardanus = (point + vector2d).cardanus

        if isCenterMassMove:
            self._center.cardanus = (self._center + vector2d).cardanus

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        """
        Поворот примитива c использованием координат точек примитива, взятых с канвы

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
        centerPoint = VectorComplex.getInstance()
        super().__init__(canvas, tuple(), centerPoint)
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

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        # отметку центра вращать не надо, так как бессмысленно вращать окружность.
        pass


class Arrow(AbstractOnCanvasMark):
    """
    Отображение иллюстративной стрелки на канве
    """
    # def __init__(self, canvas: Canvas, *args, **kwargs):
    def __init__(self, canvas: Canvas, start: VectorComplex, finish: VectorComplex, width: float, color: str, pinPoint=None):
        """
        :param canvas: канва
        :param start: начальная точка
        :param finish: конечная точка
        :param width: ширина линии
        :param color: цвет стрелки
        :param pinPoint: ось вращения
        :type pinPoint: VectorComplex
        """
        self.__pinPoint = pinPoint if pinPoint is not None else VectorComplex.getInstance()
        super().__init__(canvas, (start, finish), self.__pinPoint)

        self.__width = width
        self.__color = color


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
    def __init__(self, canvas: Canvas, start: VectorComplex, text: str, textAnchor, tkinterColor: str):
        """
        :param canvas: канва
        :param start: координаты точки крепления к канве
        :param text: текст
        :param textAnchor: положение текста относительно точки прикрепления к канве
        :param tkinterColor: текста
        """
        super().__init__(canvas, (start, start), start)

        self.__textAnchor = textAnchor
        self._text = text
        self.__color = tkinterColor

    def createOnCanvas(self):
        if self._objOnCanvasId is None:
            self._objOnCanvasId = self._canvas.create_text(self._points[0].x, self._points[0].y, text=self._text,
                                                           anchor=self.__textAnchor, fill=self.__color)
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

    def preliminaryMove(self, vector2d: VectorComplex, isCenterMassMove=False):
        pass

    def move(self, pinPoint: VectorComplex):
        pass

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        pass


class PsevdoArcArrow(AbstractOnCanvasMark):
    """
    Отображение иллюстративной дуговой стрелки на канве
    """
    CLOCKWISE = "ClockWise"
    COUNTERCLOCKWISE = "CounterClockWise"
    ZERO = "ZeroValue"
    ArrowDirection = {CLOCKWISE, COUNTERCLOCKWISE, ZERO}
    def __init__(self, canvas: Canvas, pinPoint: VectorComplex, tkinterColor: str):
        """

        :param canvas: канва
        :param pinPoint: точка привязки дуговой стрелки к канве
        :param tkinterColor: цвет дуговой стрелки
        """
        super().__init__(canvas, (), pinPoint)

        # начальный угол сектора дуги
        self.__startAngle = 45
        # конечный угол сектора дуги
        self.__finishAngle = 90
        # ширина дуговой стрелки
        self.__width = 2
        # цвет стрелки
        # self.__color = "green"
        self.__color = tkinterColor
        # self.__temp = self._canvas.background
        # радиус кривизны дуги
        self.__circleRadius = 30
        # направление дуговой стрелки
        self.__arrowDirection: PsevdoArcArrow.ArrowDirection = PsevdoArcArrow.COUNTERCLOCKWISE
        # видимость нулевой стрелки
        # если нулевая стрелка невидима, значит видима угловая стрелка, и наоборот
        # self.__zeroArrowVisible = False

        # вычисляем точки стрелки по левой стороне (положение по умолчанию, а так же по парковке)
        self.__arrowPoints = [*self.__calcMiniArrowToLeftPoints()]

        # self.zeroArrowPoints = []
        # if self.__arrowDirection == PsevdoArcArrow.CLOCKWISE:
        #     self.changeArrowDirection()

        self.__doNotExist = -1
        self.__listObjectsId = {"arc": self.__doNotExist, "arrow": self.__doNotExist, "zero": self.__doNotExist}

    @property
    def direction(self):
        return self.__arrowDirection

    def __calcMiniArrowToLeftPoints(self):
        """
        Рассчёт координат мини стрелки на конце дуги направленной против часовой стрелки

        :return: координаты начальной и конечной точек дуги
        :rtype tuple:
        """
        # 1. Рассчитать координаты радиус-вектора конца дуги
        # - создать радиус вектор (R, 0)
        # - повернуть его на стартовый угол + финишный угол
        # 2. Рассчитать координаты перпендикулярного ему вектора
        # - повернуть итоговый вектор из п. 1 далее на 90 градусов
        # - сместить полученный вектор, вдоль вектора из п. 1 к его концу
        # 3. Минимизировать длину вектора из п. 2.
        # 4. Готово.
        vector = VectorComplex.getInstance(self.__circleRadius, 0.)
        # Так как система координат канвы - левая, то поворот по против часовой стрелки является отрицательным
        finishVector = VectorComplex.getInstanceC(vector.cardanus * rect(1., radians(- self.__startAngle - self.__finishAngle)))
        ortogonalVector = VectorComplex.getInstanceC(finishVector.cardanus * rect(1., - pi / 2))
        ortogonalVector = ortogonalVector / abs(ortogonalVector.cardanus)
        arcTangentStart = finishVector
        arcTangentFinish = ortogonalVector + finishVector
        return arcTangentStart, arcTangentFinish

    def __calcMiniArrowInCenter(self):
        """
        Расчёт координат стрелки, показывающей отсутствие изменений угловой величины

        :return: координаты начальной и конечной точек стрелки
        :rtype tuple:
        """
        # 1. Расчитать координаты вертикального радиус-вектора (к центральной точке дуги.
        # 2. Расчитать начало линии будущей стрелке (возможно единичный вектор?)
        # 3. Возвратить координаты начала и конца вектора срединной стрелки.
        finishPoint = VectorComplex.getInstance(0., - self.__circleRadius)
        startPoint = VectorComplex.getInstance(0., - self.__circleRadius + 1)
        return startPoint, finishPoint

    def changeArrowDirection(self, direction=None):
        """ Перенос стрелки на другой конец дуги или в её центр

        :param direction: направление стрелки (по часовой или против), по умолчанию: перекидываем на другой конец
        """
        for value in self.__listObjectsId.values():
            if value == self.__doNotExist:
                raise RuntimeError("One of elements of arc arrow does not exist on canvas. "
                                   "Use this method after createOnCanvas method.")
        if direction is None:
            if self.__arrowDirection == PsevdoArcArrow.ZERO:
                # нельзя изменить направление на "противоположное", так как у нулевой величины нет "противоположного"
                raise RuntimeError("Could`t change direction, because current direction is ZERO. "
                                 "You should be change from CLOCKWISE to COUNTERCLOCKWISE or "
                                 "from COUNTERCLOCKWISE to CLOCKWISE.")
            # действие по умолчанию: перекидываем стрелку с одного конца дуги на другой
            self.__arrowPoints[0].decart = (- self.__arrowPoints[0].x, self.__arrowPoints[0].y)
            self.__arrowPoints[1].decart = (- self.__arrowPoints[1].x, self.__arrowPoints[1].y)
            self.__arrowDirection = PsevdoArcArrow.COUNTERCLOCKWISE \
                if self.__arrowDirection == PsevdoArcArrow.CLOCKWISE else PsevdoArcArrow.CLOCKWISE
        else:
            # перекидывание стрелки на строго определённый конец дуги
            if direction == PsevdoArcArrow.ZERO:
                # угловая величина равна нулю
                # паркуем угловую стрелку по направлению против часовой стрелки
                self.changeArrowDirection(PsevdoArcArrow.COUNTERCLOCKWISE)
                # self.changeArrowDirection(PsevdoArcArrow.COUNTERCLOCKWISE)
                self.__arrowDirection = PsevdoArcArrow.ZERO
                # делаем угловую стрелку невидимой
                self._canvas.itemconfig(self.__listObjectsId["arrow"], state="hidden")
                # делаем нулевую стрелку видимой
                self._canvas.itemconfig(self.__listObjectsId["zero"], state="normal")
                # self.__zeroArrowVisible = True
                # pass
            else:
                self._canvas.itemconfig(self.__listObjectsId["zero"], state="hidden")
                self._canvas.itemconfig(self.__listObjectsId["arrow"], state="normal")
                if direction == PsevdoArcArrow.CLOCKWISE:
                    self.__arrowPoints[0].decart = (abs(self.__arrowPoints[0].x), self.__arrowPoints[0].y)
                    self.__arrowPoints[1].decart = (abs(self.__arrowPoints[1].x), self.__arrowPoints[1].y)
                    self.__arrowDirection = PsevdoArcArrow.CLOCKWISE
                elif direction == PsevdoArcArrow.COUNTERCLOCKWISE:
                    self.__arrowPoints[0].decart = (- abs(self.__arrowPoints[0].x), self.__arrowPoints[0].y)
                    self.__arrowPoints[1].decart = (- abs(self.__arrowPoints[1].x), self.__arrowPoints[1].y)
                    self.__arrowDirection = PsevdoArcArrow.COUNTERCLOCKWISE

    def createOnCanvas(self):
        """
        Создать примитивы на канве
        """
        if self.__listObjectsId["arc"] == self.__doNotExist:
            self.__listObjectsId["arc"] = self._canvas.create_arc(self._center.x - self.__circleRadius,
                                                                  self._center.y - self.__circleRadius,
                                                                  self._center.x + self.__circleRadius,
                                                                  self._center.y + self.__circleRadius,
                                                                  start=self.__startAngle, extent=self.__finishAngle,
                                                                  width=self.__width, outline=self.__color, style=ARC)

        if self.__listObjectsId["arrow"] == self.__doNotExist:
            coords = []
            for i in range(len(self.__arrowPoints)):
                # смещаем стрелку из нулевой позиции в точку, связанную с центром дуги
                self.__arrowPoints[i] += self._center
                # получаем пару координат
                pair = self.__arrowPoints[i].decart
                # собираем список координат
                coords.extend(pair)

            self.__listObjectsId["arrow"] = self._canvas.create_line(coords,
                                                                     width=self.__width, fill=self.__color, arrow=LAST)

        if self.__listObjectsId["zero"] == self.__doNotExist:
            start, finish = self.__calcMiniArrowInCenter()
            # пара координат начала линии
            start = (start + self._center).decart
            # пара координат конца линии
            finish = (finish + self._center).decart
            coords = [*start]
            # список координат для отрисовки линии
            coords.extend(finish)
            self.__listObjectsId["zero"] = self._canvas.create_line(coords,
                                                                     width=self.__width, fill=self.__color, arrow=LAST)
            # self._canvas.itemconfig(self.__listObjectsId["zero"], fill=self.__listObjectsId["zero"].background)
            self._canvas.itemconfig(self.__listObjectsId["zero"], state="hidden")
            # print(self._canvas.)

    def preliminaryMove(self, vector2d: VectorComplex, isCenterMassMove=False):
        pass

    def move(self, pinPoint: VectorComplex):
        pass

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        pass

class ArcArrowAndText:
    """
    Дуговая стрелка углового параметра движения и легенда этого параметра
    """
    def __init__(self, canvas: Canvas, coords: VectorComplex, header: str, value: float, format: str, tkinterColor: str):
        """

        :param canvas: канва
        :param coords: коориднаты точки крепления к канве
        :param header: заголовок (что за величина)
        :param value: значение величины
        :param format: формат строки отображения величины
        :param tkinterColor: цвет текста и стрелки
        """
        self.__canvas = canvas
        self.__coords = coords
        self.__header = header
        self.__value = value
        self.__format = format
        self.__color = tkinterColor

        self.__headerObject = Text(self.__canvas, self.__coords + VectorComplex.getInstance(0, -50), self.__header, N, self.__color)
        self.__legendObject = Text(self.__canvas, self.__coords + VectorComplex.getInstance(0, -20), self.__format, N, self.__color)
        self.__arrowObject = PsevdoArcArrow(self.__canvas, self.__coords, self.__color)

    def createOnCanvas(self):
        self.__headerObject.createOnCanvas()
        self.__legendObject.createOnCanvas()
        self.__arrowObject.createOnCanvas()

    @property
    def text(self):
        return self.__legendObject.text

    @text.setter
    def text(self, value):
        self.__legendObject.text = value

    @property
    def direction(self):
        return self.__arrowObject.direction

    @direction.setter
    def direction(self, value=None):
        self.__arrowObject.changeArrowDirection(value)


class LineArrowInCirle(AbstractOnCanvasMark):
    """
    Стрелка, вращающаяся вокруг точки, являющейся её серединой
    """
    def __init__(self, canvas: Canvas, centerPoint: VectorComplex, tkinterColor: str):
        """

        :param canvas: канва
        :param centerPoint: точка крепления стрелки к канве (середина стрелки)
        :param tkinterColor: цвет стрелки и текста
        """
        super().__init__(canvas, (), centerPoint)

        # ширина стрелки
        self.__width = 2
        # цвет стрелки
        # self.__color = "green"
        self.__color = tkinterColor
        # длина стрелки
        self.__arrowLength = 30
        # направление стрелки в СКК
        self.__arrowDirection = VectorComplex.getInstance(0., -1)

        # вычисляем точки стрелки (положение по умолчанию)
        self._points = [*self.__calcArrowPoints()]

        self.__doNotExist = -1
        self._objOnCanvasId = self.__doNotExist

    @property
    def direction(self):
        return self.__arrowDirection

    def __calcArrowPoints(self):
        """ Координаты стрелки для канвы """
        start = -self.__arrowDirection * (self.__arrowLength / 2) + self._center
        finish = self.__arrowDirection * (self.__arrowLength / 2) + self._center

        return start, finish

    def __pointsToList(self):
        """ Перевод координат VectorComplex в сплошной лист для применения в функциях канвы. """
        result = []
        for value in self._points:
            result.extend(value.decart)
        return result

    def changeArrowDirection(self, direction: VectorComplex):
        """ Изменение направления стрелки.

        :param direction: новое направление стрелки в СКК
        """
        # direction = VectorComplex.getInstance() if direction is None else direction

        # приводим к единичному вектору с проверкой на нулевой вектор, а то может быть ошибка деления на ноль
        self.__arrowDirection = direction / abs(direction) if abs(direction) != 0 else self.__arrowDirection
        # координаты начала и конца линиии-стрелки
        self._points = self.__calcArrowPoints()

        self._canvas.coords(self._objOnCanvasId, *self.__pointsToList())

    def createOnCanvas(self):
        if self._objOnCanvasId == self.__doNotExist:
            self._objOnCanvasId = self._canvas.create_line(*self.__pointsToList(),
                                                                 width=self.__width, fill=self.__color, arrow=LAST)

    def preliminaryMove(self, vector2d: VectorComplex, isCenterMassMove=False):
        pass

    def move(self, pinPoint: VectorComplex):
        pass

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        pass

class LineArrowAndText:
    """
    Стрелка линейного параметра движения и легенда этого параметра
    """
    def __init__(self, canvas: Canvas, coords: VectorComplex, header: str, value: float, format: str, tkinterColor: str):
        """

        :param canvas: канва
        :param coords: координаты точки крепления (середина стрелки)
        :param header: заголовок (что за величина)
        :param value: цифровое значение величины
        :param format: формат строки отображения цифорового значения величины
        :param tkinterColor: цвет текста и стрелки
        """
        self.__canvas = canvas
        self.__coords = coords
        self.__header = header
        self.__value = value
        self.__format = format
        self.__color = tkinterColor

        self.__headerObject = Text(self.__canvas, self.__coords + VectorComplex.getInstance(0, -30), self.__header, N, self.__color)
        self.__legendObject = Text(self.__canvas, self.__coords + VectorComplex.getInstance(0, 10), self.__format, N, self.__color)
        self.__arrowObject = LineArrowInCirle(self.__canvas, self.__coords,self.__color)

    def createOnCanvas(self):
        self.__headerObject.createOnCanvas()
        self.__legendObject.createOnCanvas()
        self.__arrowObject.createOnCanvas()

    @property
    def text(self):
        # todo убрать за ненадобностью?
        return self.__legendObject.text

    @text.setter
    def text(self, value):
        # todo убрать за ненадобностью?
        self.__legendObject.text = value

    @property
    def direction(self):
        # todo убрать за ненадобностью?
        return self.__arrowObject.direction

    @direction.setter
    def direction(self, value: VectorComplex):
        # todo убрать за ненадобностью?
        self.__arrowObject.changeArrowDirection(value)

    def setInfo(self, value: float, vector: VectorComplex):
        """
        Установить новые данные и направление стрелки.

        :param value: значение величины
        :param vector: вектор направления стрелки в СКК
        :return:
        """
        self.__legendObject.text = self.__format.format(value)
        self.__arrowObject.changeArrowDirection(vector)


