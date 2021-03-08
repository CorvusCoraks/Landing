""" Модуль визуализации происходящего с испытуемым объектом. """
from tkinter import Tk, Canvas, colorchooser, Toplevel
from queue import Queue
from point import VectorComplex
from stage import Stage, Sizes
from decart import fromOldToNewCoordSystem, pointsListToNewCoordinateSystem
from torch import tensor
from cmath import polar
from itertools import chain

from cmath import exp, rect

# X_DIR = 0
# Y_DIR = 1


class Window():
    """
    Класс окна вывода увеличенного изображения ступени и числовых характеристик
    """
    # def __init__(self, frameRate: int, anyQueue: Queue):
    def __init__(self, root: Tk, frameRate: int, anyQueue: Queue):
        """

        :param function: callback
        :param anyQueue: очередь для передачи данных одного фрейма движения ступени
        """
        # self.__getDataFunction = function
        self.__anyQueue = anyQueue
        self.__frameRate = frameRate # частота кадров
        size = 600
        # self.__root = Tk()
        self.__root = Toplevel(root)
        self.__root.title("Stage view")
        self.__canvas = Canvas(self.__root, width=size, height=size)
        # canvas.
        self.__canvas.pack()
        self.__stage = FirstStage2(self.__canvas)
        # self.__root.after(1000, function, self.__root)
        # self.__root.after(1000, function, self.__root, 0, True)
        self.__root.after(self.__frameRate, self.__draw)
        self.__root.mainloop()

    def canvas(self):
        return self.__canvas

    def __draw(self):
        """ метод для периодической перерисовки объектов на канве """
        print("In __draw")

        # move_to = 0.
        # angle_to = 0.
        transform = None

        # получение данных из внешних источников self.__anyQueue
        # self.__getDataFunction()
        if not self.__anyQueue.empty():
            # print(self.__anyQueue.get())
            transform = self.__anyQueue.get()
        # print(self.__anyQueue.get())

        # отрисовка нового положения объектов на основании полученных данных из self.__anyQueue
        if transform is not None:
            # рисовать
            self.__stage.draw()
            # двигать
            self.__stage.move(transform.vector2d)
            # вращать
            self.__stage.rotate(transform.orientation2d)
            # print(transform.orientation2d.cardanus)
            # print(transform.text)
        # self.__stage.

        # запускаем отрисовку цикл
        self.__root.after(self.__frameRate, self.__draw)


class PoligonWindow():
    """
    Окно испытательного полигона, на котором рисуется траектория

    """
    def __init__(self, frameRate: int, queue: Queue, poligonWidth: float, poligonHeigt: float, poligonScale: float):
        """

        :param frameRate: частота кадров (и поступления данных в очередь)
        :param queue: очередь данных для отрисовки траектории в главном окне.
        :param poligonWidth: ширина испытательного полигона (точка посадки находится посередине)
        :param poligonHeigt: высота испытательного полигона (от уровня грунта)
        :param poligonScale: масштаб отображения полигона. Тысяч метров на одну точку.
        """
        self.__frameRate = frameRate
        self.__queue = queue
        # Очередь для передачи данных в дочернее окно
        self.__subQueue = Queue()
        # size = 600
        self.__root = Tk()
        self.__root.geometry("+300+100")
        self.__root.title("Trajectory")
        self.__canvas = Canvas(self.__root, width=poligonWidth, height=poligonHeigt)
        self.__canvas.pack()
        self.__createStaticMarks()
        self.__root.after(self.__frameRate, self.__draw)
        # self.__root.mainloop()

        # Окно увеличенного изображения ступени в просессе посадки
        self.__stageWindow = Window(self.__root, frameRate, self.__subQueue)

    def __draw(self):
        # метод для периодического вызова и отрисовки на канве (точка траектории, данные по высоте, тангажу, крену и пр)
        transform = None

        # получение данных из внешних источников self.__anyQueue
        if not self.__queue.empty():
            # print(self.__anyQueue.get())
            transform = self.__queue.get()
            # прозрачно ретранслируем блок данных в следующее окно
            self.__subQueue.put(transform)

        # отрисовка нового положения объектов на основании полученных данных из self.__anyQueue
        if transform is not None:
            # рисовать
            # self.__stage.draw()
            # двигать
            # self.__stage.move(transform.vector2d)
            # вращать
            # self.__stage.rotate(transform.orientation2d)
            # print(transform.orientation2d.cardanus)
            # print(transform.text)
            pass

        # запускаем отрисовку цикл
        self.__root.after(self.__frameRate, self.__draw)

    def __createStaticMarks(self):
        # метод расставляет необходимые отметки по полигону (точка сброса ступени, точка посадки ступени и пр.)
        pass


class FirstStage():
    """
    Класс изображения первой ступени
    """
    #
    # сначала необходимо отрисовать (создать) объект на канве:
    # draw()
    #
    # в дальнейшем, движение и поворот объекта на канве реализуется последовательным применением этих двух методов
    # move()
    # rotate()
    #
    # метод draw() можно вызывать неоднократно, так как объект на канве создаётся только при ПЕРВОМ вызове метода.
    # При последующих вызовах новые объекты не создаются, а методы move() и rotate() применяются к объекту,
    # который был создан при ПЕРВОМ вызове метода draw()
    #
    # Ступень представляет из себя связанный набор стандартных примитивов (в основном многоугольники)
    def __init__(self, canvas: Canvas):
        self.__canvas = canvas
        #
        # Изображение ступени формируется в рамках локальной системы координат привязанной к какой либо ключевой
        # точке самой ракеты.
        #
        # Установка ракеты в позицию на холсте приозиводится за счёт указания вектора, привязанного к системе
        # координат холста.
        # self.__massCenterInCanvasVector = VectorComplex.getInstance(0., 0.)
        #
        # Так как при создании ступень стоит вертикально, данный вектор (вектор продольной оси) направлен по оси Y
        # в системе отсчёта канвы
        # self.__directionVector = Point(0., 1.)
        # todo возможно (0, -1)?
        self.__directionVector = VectorComplex.getInstance(0., 1.)
        #
        # Задаём координаты графических элементов ступени относительно её ЦЕНТРА МАСС
        #

        # Все примитивы изначально рисуются в привязке к началу координат канвы, с целью упрощения задания координат
        # ключевых точек.
        # В последствии, при не обходимости, примитивы перемещаются в нужное положение целиком.

        # центр масс (центр вращения) в системе координат канвы
        #
        self.__massCenter = VectorComplex.add(VectorComplex.getInstance(Stage.width/2, Stage.height), Stage.m1vector)
        # массив всех примитивов ступени
        self.__allPrimitives = []

        # корпус ступени
        # Верхний левый угол ступени находится в начале координат канвы. В этом положении ступень находится до конца
        # сборки всех примитивов
        self.__tank = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0., 0.),
                          VectorComplex.getInstance(Stage.width, Stage.height),
                          self.__massCenter)
        self.__allPrimitives.append(self.__tank)

        # верхний левый маневровый двигатель
        # создание в нулевой позиции
        self.__topLeftJet = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(10, 5),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__topLeftJet.preliminaryMove(VectorComplex.getInstance(-10, 0))
        self.__allPrimitives.append(self.__topLeftJet)

        # верхний правый маневровый двигатель
        # создание в нулевой позиции
        self.__topRightJet = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(10, 5),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__topRightJet.preliminaryMove(VectorComplex.getInstance(10, 0))
        self.__allPrimitives.append(self.__topRightJet)

        # нижний левый маневровый двигатель
        # создание в нулевой позиции
        self.__downLeftJet = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(10, 5),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__downLeftJet.preliminaryMove(VectorComplex.getInstance(-10, 25))
        self.__allPrimitives.append(self.__downLeftJet)

        # нижний правый маневровый двигатель
        # создание в нулевой позиции
        self.__downRightJet = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(10, 5),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__downRightJet.preliminaryMove(VectorComplex.getInstance(10, 25))
        self.__allPrimitives.append(self.__downRightJet)

        # # координаты центра масс (центр вращения) в системе отсчёта канвы.
        # # self.__massCenter = Point(55, 20)
        # self.__massCenter = Point(5, 20)

        # # все примитивы, составляющие объект
        # self.__allPrimitives = []

        # # корпус ступени (прямоугольник размера 10х30)
        # self.__tank = PoligonRectangle(self.__canvas).create2points(Point(0, 0), Point(10, 30), self.__massCenter)
        # # self.__tank = PoligonRectangle(self.__canvas).create2points(Point(50, 0), Point(60, 30), self.__massCenter)
        # self.__allPrimitives.append(self.__tank)

        # # верхний левый маневровый двигатель
        # # создание в нулевой позиции
        # self.__topLeftJet = PoligonRectangle(self.__canvas).create2points(Point(0, 0), Point(10, 5), self.__massCenter)
        # # смещение примитива в нужную позицию
        # self.__topLeftJet.virtualMove(Point(-10, 0))
        # # self.__topLeftJet = PoligonRectangle(self.__canvas).create2points(Point(40, 0), Point(50, 5), self.__massCenter)
        # self.__allPrimitives.append(self.__topLeftJet)

        # # верхний правый маневровый двигатель
        # # создание в нулевой позиции
        # self.__topRightJet = PoligonRectangle(self.__canvas).create2points(Point(0, 0), Point(10, 5), self.__massCenter)
        # # смещение примитива в нужную позицию
        # self.__topRightJet.virtualMove(Point(10, 0))
        # self.__allPrimitives.append(self.__topRightJet)

        # # нижний левый маневровый двигатель
        # # создание в нулевой позиции
        # self.__downLeftJet = PoligonRectangle(self.__canvas).create2points(Point(0, 0), Point(10, 5), self.__massCenter)
        # # смещение примитива в нужную позицию
        # self.__downLeftJet.virtualMove(Point(-10, 25))
        # self.__allPrimitives.append(self.__downLeftJet)
        #
        # # нижний правый маневровый двигатель
        # # создание в нулевой позиции
        # self.__downRightJet = PoligonRectangle(self.__canvas).create2points(Point(0, 0), Point(10, 5), self.__massCenter)
        # # смещение примитива в нужную позицию
        # self.__downRightJet.virtualMove(Point(10, 25))
        # self.__allPrimitives.append(self.__downRightJet)

    def draw(self):
        """
        Рисовать (создать) ступерь на канве. Создаётся единственно только при ПЕРВОМ вызове.
        """
        for primitive in self.__allPrimitives:
            primitive.draw()

    def move(self, newMassCenter: VectorComplex):
        """
        Двигать ступень.

        :param newMassCenter:
        """
        # moveVector = Point()
        # moveVector.cardanus = newMassCenter.cardanus - self.__massCenter.cardanus
        moveVector = VectorComplex.sub(newMassCenter, self.__massCenter)

        for primitive in self.__allPrimitives:
            primitive.move(moveVector)

        self.__massCenter = newMassCenter

    def rotate(self, newVector: VectorComplex):
        """
        Вращать ступень.

        :param newVector:
        """
        for primitive in self.__allPrimitives:
            primitive.rotate(newVector, self.__directionVector)

        # Обновляем значение
        self.__directionVector = newVector


class FirstStage2():
    """
    Класс изображения первой ступени
    """
    #
    # сначала необходимо отрисовать (создать) объект на канве:
    # draw()
    #
    # в дальнейшем, движение и поворот объекта на канве реализуется последовательным применением этих двух методов
    # move()
    # rotate()
    #
    # метод draw() можно вызывать неоднократно, так как объект на канве создаётся только при ПЕРВОМ вызове метода.
    # При последующих вызовах новые объекты не создаются, а методы move() и rotate() применяются к объекту,
    # который был создан при ПЕРВОМ вызове метода draw()
    #
    # Ступень представляет из себя связанный набор стандартных примитивов (в основном многоугольники)
    def __init__(self, canvas: Canvas):
        self.__canvas = canvas
        # Алгоритм сборки.
        # -----
        # Во время графической сборки примитивов, все вектора отсчитываются (для простоты) от левого верхнего угла
        # центрального блока. То есть, левый верхний угол центрального блока находится в начале координат канвы (1).
        #
        # После сборки, координаты ступени пересчитываются в точку координат её центра масс (2)
        #
        # Затем ступень переносится в своё начальное положение (3)
        # -----
        # Установка ракеты в позицию на холсте приозиводится за счёт указания вектора центра масс ступени,
        # привязанного к системе координат холста.
        # В данном случае, установка произведена так, чтобы верхний левый угол центрального блока
        # совпал с началом координат канвы
        self.__massCenter \
            = VectorComplex.getInstance(Sizes.widthCenterBlock / 2, Sizes.heightCenterBlock * 2/3)
        #
        # Так как при создании ступень стоит вертикально, данный вектор (вектор продольной оси) направлен по оси Y
        # в системе отсчёта канвы
        # self.__directionVector = Point(0., 1.)
        # todo возможно (0, -1)?
        self.__directionVector = VectorComplex.getInstance(0., -1.)
        #
        # Задаём координаты графических элементов ступени относительно её ЦЕНТРА МАСС
        #

        # Все примитивы изначально рисуются в привязке к началу координат канвы, с целью упрощения задания координат
        # ключевых точек.
        # В последствии, при не обходимости, примитивы перемещаются в нужное положение целиком.

        # центр масс (центр вращения) в системе координат канвы
        #
        # self.__massCenter = VectorComplex.add(VectorComplex.getInstance(Stage.width/2, Stage.height), Stage.m1vector)

        # массив всех примитивов ступени
        self.__allPrimitives = []

        # корпус ступени
        # Верхний левый угол ступени находится в начале координат канвы. В этом положении ступень находится до конца
        # сборки всех примитивов
        self.__tank = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0., 0.),
                          VectorComplex.getInstance(Sizes.widthCenterBlock, Sizes.heightCenterBlock),
                          self.__massCenter)
        self.__allPrimitives.append(self.__tank)

        # верхний левый маневровый двигатель
        # создание в нулевой позиции
        self.__topLeftJet = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthJet, Sizes.heightJet),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__topLeftJet.preliminaryMove(VectorComplex.getInstance(- Sizes.widthJet, 0))
        self.__allPrimitives.append(self.__topLeftJet)

        # верхний правый маневровый двигатель
        # создание в нулевой позиции
        self.__topRightJet = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthJet, Sizes.heightJet),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__topRightJet.preliminaryMove(VectorComplex.getInstance(Sizes.widthCenterBlock, 0))
        self.__allPrimitives.append(self.__topRightJet)

        # нижний левый маневровый двигатель
        # создание в нулевой позиции
        self.__downLeftJet = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthJet, Sizes.heightJet),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__downLeftJet.preliminaryMove(VectorComplex.getInstance(- Sizes.widthJet, Sizes.heightCenterBlock - Sizes.heightJet))
        self.__allPrimitives.append(self.__downLeftJet)

        # нижний правый маневровый двигатель
        # создание в нулевой позиции
        self.__downRightJet = PoligonRectangle2(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthJet, Sizes.heightJet),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__downRightJet.preliminaryMove(VectorComplex.getInstance(Sizes.widthCenterBlock, Sizes.heightCenterBlock - Sizes.heightJet))
        self.__allPrimitives.append(self.__downRightJet)

    def draw(self):
        """
        Рисовать (создать) ступерь на канве. Создаётся единственно только при ПЕРВОМ вызове.
        """
        for primitive in self.__allPrimitives:
            primitive.draw()

    def move(self, newMassCenter: VectorComplex):
        """
        Двигать ступень.

        :param newMassCenter:
        """
        # moveVector = Point()
        # moveVector.cardanus = newMassCenter.cardanus - self.__massCenter.cardanus
        moveVector = VectorComplex.sub(newMassCenter, self.__massCenter)

        for primitive in self.__allPrimitives:
            primitive.move(moveVector)

        self.__massCenter = newMassCenter

    def rotate(self, newVector: VectorComplex):
        """
        Вращать ступень.

        :param newVector:
        """
        for primitive in self.__allPrimitives:
            primitive.rotate(newVector, self.__directionVector)

        # Обновляем значение
        self.__directionVector = newVector


class PoligonRectangle2():
    def __init__(self, canvas: Canvas):
        """
        :param canvas: канва, на которой будет выводится данный многоугольник
        """
        self.__canvas = canvas
        # Список точек многоугольника типа VectorComplex
        self.__points = []
        # Идентификатор объекта на канве
        self.__objOnCanvasId = None
        # Точка, во круг которой осуществляется поворот многоугольника
        self.__center = VectorComplex.getInstance()
        # вектор ориентации примитива. Изначально направлен по оси Y канвы
        # self.__directionVector = Point(0., 1.)

    def create2points(self, topleft: VectorComplex, downright: VectorComplex, center: VectorComplex):
        """
        Создание прямоугольника по двум точкам

        :param topleft:
        :param downright:
        :param center: центр вращения примитива
        :return:
        """
        self.__points = [topleft, VectorComplex.getInstance(downright.x, topleft.y),
                         downright, VectorComplex.getInstance(topleft.x, downright.y)]
        self.__center = center
        return self

    # # todo метод не используется. Убрать?
    # def create(self, points: list, center: Point):
    #     """
    #     Создание многоугольника из списка точек. Прямые углы прямоугольника на совести создателя.
    #
    #     :param points: list of points Point-type
    #     :return:
    #     """
    #     for value in enumerate(points):
    #         if value is not Point:
    #             raise TypeError("Expected point.Point type, but {} founded".format(type(value)))
    #
    #     self.__points = [p for p in points]
    #     self.__center = center
    #     return self

    def move(self, vector2d: VectorComplex):
        """
        Двигать примитив.

        :param vector2d: вектор, в направлении и на величину которого двигать примитив.
        """
        if self.__objOnCanvasId is not None:
            # перемещаем по канве
            self.__canvas.move(self.__objOnCanvasId, vector2d.x, vector2d.y)
            # пересчитываем положение центра вращения
            # self.__center = Point(self.__center.cardanus + vector2d.cardanus)
            self.__center = VectorComplex.getInstanceC(self.__center.cardanus + vector2d.cardanus)

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
        for _, point in enumerate(self.__points):
            point.cardanus = point.cardanus + vector2d.cardanus
            # point.cardanus = VectorComplex.add(point, vector2d).cardanus

        if isCenterMassMove:
            self.__center = self.__center.cardanus + vector2d.cardanus

    def rotate(self, newAxisVector: VectorComplex, oldAxisVector: VectorComplex):
        """
        Поворот примитива.

        :param newAxisVector: новый вектор оси ступени
        :param oldAxisVector: старый вектор оси ступени
        """
        # получить координаты точек объекта в системе координат канвы
        current = self.__canvas.coords(self.__objOnCanvasId)
        points = []
        # Преобразовать координаты точек в объекты типа VectorComplex в СК канвы
        # for i in range(len(self.__points)):
        #     points.append(Point(current[i * 2], current[i * 2 + 1]))
        for i in range(len(self.__points)):
            points.append(VectorComplex.getInstance(current[i * 2], current[i * 2 + 1]))
        # Пересчитать координаты точек объектов из системы канвы в систему центра тяжести
        # (координатные оси сонаправлены)
        # points = toNewOrigin(points, self.__center)
        # points = fromOldToNewCoordSystem(points, VectorComplex(tensor([- self.__center.x, - self.__center.y])), 0.)
        points = pointsListToNewCoordinateSystem(points, self.__center)
        # Расчитать новые точки через поворот вокруг центра тяжести
        # Угол поворота из старого положения
        # alpha_complex = Point()
        # alpha_complex.cardanus = newAxisVector.cardanus / oldAxisVector.cardanus
        alpha_complex = VectorComplex.getInstanceC(newAxisVector.cardanus / oldAxisVector.cardanus)
        # __, phi = polar(alpha_complex.cardanus)
        # print("Угол поворота: {}, {}".format(phi, alpha_complex.cardanus))
        # новые координаты точек объекта в системе координат относительно точки поворота
        new_points = []
        for value in points:
            # point = value.cardanus * alpha_complex
            # newPoint = Point()
            # newPoint.cardanus = value.cardanus * alpha_complex.cardanus
            newPoint = VectorComplex.getInstanceC(value.cardanus * alpha_complex.cardanus)
            new_points.append(newPoint)
        # points = [value.cardanus * alpha_complex for value in points]
        # Новые точки пересчитать обратно в систему координат канвы
        # new_points = toNewOrigin(new_points, Point(-self.__center.x, -self.__center.y))
        new_points = pointsListToNewCoordinateSystem(new_points, VectorComplex.getInstance(- self.__center.x, - self.__center.y))
        # Обновить координаты точек в объекте (будет произведена автоматическое визуальное изменение)
        canvas_points = []
        for value in new_points:
            canvas_points.append(value.x)
            canvas_points.append(value.y)
        self.__canvas.coords(self.__objOnCanvasId, canvas_points)

    def draw(self):
        """
        Рисовать примитив (если он не существует) на канве
        """
        if self.__objOnCanvasId is None:
            # Если примитив ещё нет на канве (то есть, он ещё ни разу не отрисовывался,
            # то можно его создавать и рисовать)
            # self.__points[0].decart
            # plain лист ключевых точек примитива (функция канвы только в таком виде воспринимает)
            coord_list = [value.decart for value in self.__points]
            # рисуем примитив на канве
            # так как примитив, фактически, создаётся на канве, то для конкретного примитива эта функция применяется
            # только один раз. Дальнейшие действия с примитивом делаются через его идентификатор,
            # который возвращает этот метод.
            self.__objOnCanvasId = self.__canvas.create_polygon(coord_list, fill="", outline="black")
            # print(self.__canvas.coords(self.__objOnCanvasId))


# class PoligonRectangle():
#     def __init__(self, canvas: Canvas):
#         """
#         :param canvas: канва, на которой будет выводится данный многоугольник
#         """
#         self.__canvas = canvas
#         # Список точек многоугольника типа Point
#         self.__points = []
#         # Идентификатор объекта на канве
#         self.__objOnCanvasId = None
#         # Точка, во круг которой осуществляется поворот многоугольника
#         self.__center = Point()
#         # вектор ориентации примитива. Изначально направлен по оси Y канвы
#         # self.__directionVector = Point(0., 1.)
#
#     def create2points(self, topleft: Point, downright: Point, center: Point):
#         """
#         Создание прямоугольника по двум точкам
#
#         :param topleft:
#         :param downright:
#         :return:
#         """
#         self.__points = [topleft, Point(downright.x, topleft.y), downright, Point(topleft.x, downright.y)]
#         self.__center = center
#         return self
#
#     def create(self, points: list, center: Point):
#         """
#         Создание многоугольника из списка точек. Прямые углы прямоугольника на совести создателя.
#
#         :param points: list of points Point-type
#         :return:
#         """
#         for value in enumerate(points):
#             if value is not Point:
#                 raise TypeError("Expected point.Point type, but {} founded".format(type(value)))
#
#         self.__points = [p for p in points]
#         self.__center = center
#         return self
#
#     def move(self, vector2d: Point):
#         """
#         Двигать примитив.
#
#         :param vector2d: вектор, в направлении и на величину которого двигать примитив.
#         """
#         if self.__objOnCanvasId is not None:
#             # перемещаем по канве
#             self.__canvas.move(self.__objOnCanvasId, vector2d.x, vector2d.y)
#             # пересчитываем положение центра вращения
#             self.__center = Point(self.__center.cardanus + vector2d.cardanus)
#
#     def virtualMove(self, vector2d: Point, centerMassMove=False):
#         """
#         Метод предварительного смещения объекта в координатной системе канвы (без реального объекта на канве)
#
#         :param vector2d: вектор смещения
#         :param centerMassMove: сдвигать центр масс объекта вместе с остальными точками
#         """
#
#         for _, point in enumerate(self.__points):
#             point.cardanus = point.cardanus + vector2d.cardanus
#
#         if centerMassMove:
#             self.__center = self.__center.cardanus + vector2d.cardanus
#
#     def rotate(self, newAxisVector: Point, oldAxisVector: Point):
#         """
#         Поворот примитива.
#
#         :param angle: угол поворота от ПРЕДЫДУЩЕГО положения объекта на канве (т. е. дельта, изменение угла)
#         """
#         # получить координаты точек объекта в системе координат канвы
#         current = self.__canvas.coords(self.__objOnCanvasId)
#         points = []
#         # Преобразовать координаты точек в объекты типа Point
#         for i in range(len(self.__points)):
#             points.append(Point(current[i * 2], current[i * 2 + 1]))
#         # Пересчитать координаты точек объектов из системы канвы в систему центра тяжести
#         points = toNewOrigin(points, self.__center)
#         # Расчитать новые точки через поворот вокруг центра тяжести
#         # Угол поворота из страрого положения
#         alpha_complex = Point()
#         alpha_complex.cardanus = newAxisVector.cardanus / oldAxisVector.cardanus
#         # __, phi = polar(alpha_complex.cardanus)
#         # print("Угол поворота: {}, {}".format(phi, alpha_complex.cardanus))
#         # новые координаты точек объекта в системе координат относительно точки поворота
#         new_points = []
#         for value in points:
#             # point = value.cardanus * alpha_complex
#             newPoint = Point()
#             newPoint.cardanus = value.cardanus * alpha_complex.cardanus
#             new_points.append(newPoint)
#         # points = [value.cardanus * alpha_complex for value in points]
#         # Новые точки пересчитать в систему координат канвы
#         new_points = toNewOrigin(new_points, Point(-self.__center.x, -self.__center.y))
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
#             # self.__points[0].decart
#             # plain лист ключевых точек примитива (функция канвы только в таком виде воспринимает)
#             coord_list = [value.decart for value in self.__points]
#             # рисуем примитив на канве
#             # так как примитив, фактически, создаётся на канве, то для конкретного примитива эта функция применяется
#             # только один раз. Дальнейшие действия с примитивом делаются через его идентификатор,
#             # который возвращает этот метод.
#             self.__objOnCanvasId = self.__canvas.create_polygon(coord_list, fill="", outline="black")
#             # print(self.__canvas.coords(self.__objOnCanvasId))


# def toNewOrigin(pointsInOld: list, newOriginInOld: Point):
#     """
#     Метод пересчёта одних декартовых координат в другие (абциссы и ординаты сонаправлены, без поворота)
#
#     :param pointsInOld: лист старых координат точек Point
#     :param newOriginInOld: координаты новой системы координат в старой
#     :return: лист новых координат
#     """
#     # Устаревший.
#     # todo вместо этойго метода использовать соответствующий из модуля decart
#     # return [Point(- newOriginInOld.x + val.x, - newOriginInOld.y + val.y) for val in pointsInOld]
#     result = []
#     for value in pointsInOld:
#         point = Point()
#         point.cardanus = - newOriginInOld.cardanus + value.cardanus
#         result.append(point)
#     # return [Point(- newOriginInOld.cardanus + val.cardanus) for val in pointsInOld]
#     return result