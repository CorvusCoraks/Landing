from tkinter import Tk, Canvas, colorchooser
from queue import Queue
from point import Point
from cmath import polar
from itertools import chain

from cmath import exp, rect

# X_DIR = 0
# Y_DIR = 1

class Window():
    """
    Класс окна вывода изображения процесса и числовых характеристик
    """
    def __init__(self, frameRate: int, anyQueue: Queue):
        """

        :param function: callback
        :param anyQueue: очередь для передачи данных одного фрейма движения ступени
        """
        # self.__getDataFunction = function
        self.__anyQueue = anyQueue
        self.__frameRate = frameRate # частота кадров
        size = 600
        self.__root = Tk()
        self.__canvas = Canvas(self.__root, width=size, height=size)
        # canvas.
        self.__canvas.pack()
        self.__stage = FirstStage(self.__canvas)
        # self.__root.after(1000, function, self.__root)
        # self.__root.after(1000, function, self.__root, 0, True)
        self.__root.after(self.__frameRate, self.__draw)
        self.__root.mainloop()

    def canvas(self):
        return self.__canvas

    def __draw(self):
        # метод для периодической перерисовки объектов на канве
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
        # Так как при создании ступень стоит вертикально, данный вектор направлен по оси Y
        # в системе отсчёта канвы
        self.__directionVector = Point(0., 1.)
        # координаты центра масс (центр вращения) в системе отсчёта канвы.
        self.__massCenter = Point(55, 20)
        # корпус ступени
        self.__tank = PoligonRectangle(self.__canvas).create2points(Point(50, 0), Point(60, 30), self.__massCenter)
        # верхний левый маневровый двигатель
        self.__topLeftJet = PoligonRectangle(self.__canvas).create2points(Point(40, 0), Point(50, 5), self.__massCenter)

    def draw(self):
        """
        Рисовать (создать) ступерь на канве. Создаётся единственно только при ПЕРВОМ вызове.
        """
        self.__tank.draw()
        self.__topLeftJet.draw()

    def move(self, newMassCenter: Point):
        """
        Двигать ступень.

        :param newMassCenter:
        """
        moveVector = Point()
        moveVector.cardanus = newMassCenter.cardanus - self.__massCenter.cardanus

        self.__tank.move(moveVector)
        self.__topLeftJet.move(moveVector)

        self.__massCenter = newMassCenter

    def rotate(self, newVector: Point):
        """
        Вращать ступень.

        :param newVector:
        """
        self.__tank.rotate(newVector, self.__directionVector)
        self.__topLeftJet.rotate(newVector, self.__directionVector)

        # Обновляем значение
        self.__directionVector = newVector


class PoligonRectangle():
    def __init__(self, canvas: Canvas):
        """
        :param canvas: канва, на которой будет выводится данный многоугольник
        """
        self.__canvas = canvas
        # Список точек многоугольника типа Point
        self.__points = []
        # Идентификатор объекта на канве
        self.__objOnCanvasId = None
        # Точка, во круг которой осуществляется поворот многоугольника
        self.__center = Point()
        # вектор ориентации примитива. Изначально направлен по оси Y канвы
        # self.__directionVector = Point(0., 1.)

    def create2points(self, topleft: Point, downright: Point, center: Point):
        """
        Создание прямоугольника по двум точкам

        :param topleft:
        :param downright:
        :return:
        """
        self.__points = [topleft, Point(downright.x, topleft.y), downright, Point(topleft.x, downright.y)]
        self.__center = center
        return self

    def create(self, points: list, center: Point):
        """
        Создание многоугольника из списка точек. Прямые углы прямоугольника на совести создателя.

        :param points: list of points Point-type
        :return:
        """
        for value in enumerate(points):
            if value is not Point:
                raise TypeError("Expected point.Point type, but {} founded".format(type(value)))

        self.__points = [p for p in points]
        self.__center = center
        return self

    def move(self, vector2d: Point):
        """
        Двигать примитив.

        :param vector2d: вектор, в направлении и на величину которого двигать примитив.
        """
        if self.__objOnCanvasId is not None:
            # перемещаем по канве
            self.__canvas.move(self.__objOnCanvasId, vector2d.x, vector2d.y)
            # пересчитываем положение центра вращения
            self.__center = Point(self.__center.cardanus + vector2d.cardanus)

    def rotate(self, newAxisVector: Point, oldAxisVector: Point):
        """
        Поворот примитива.

        :param angle: угол поворота от ПРЕДЫДУЩЕГО положения объекта на канве (т. е. дельта, изменение угла)
        """
        # получить координаты точек объекта в системе координат канвы
        current = self.__canvas.coords(self.__objOnCanvasId)
        points = []
        # Преобразовать координаты точек в объекты типа Point
        for i in range(len(self.__points)):
            points.append(Point(current[i * 2], current[i * 2 + 1]))
        # Пересчитать координаты точек объектов из системы канвы в систему центра тяжести
        points = toNewOrigin(points, self.__center)
        # Расчитать новые точки через поворот вокруг центра тяжести
        # Угол поворота из страрого положения
        alpha_complex = Point()
        alpha_complex.cardanus = newAxisVector.cardanus / oldAxisVector.cardanus
        # __, phi = polar(alpha_complex.cardanus)
        # print("Угол поворота: {}, {}".format(phi, alpha_complex.cardanus))
        # новые координаты точек объекта в системе координат относительно точки поворота
        new_points = []
        for value in points:
            # point = value.cardanus * alpha_complex
            newPoint = Point()
            newPoint.cardanus = value.cardanus * alpha_complex.cardanus
            new_points.append(newPoint)
        # points = [value.cardanus * alpha_complex for value in points]
        # Новые точки пересчитать в систему координат канвы
        new_points = toNewOrigin(new_points, Point(-self.__center.x, -self.__center.y))
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


def toNewOrigin(pointsInOld: list, newOriginInOld: Point):
    """
    Метод пересчёта одних декартовых координат в другие (абциссы и ординаты сонаправлены, без поворота)

    :param pointsInOld: лист старых координат точек Point
    :param newOriginInOld: координаты новой системы координат в старой
    :return: лист новых координат
    """
    # Устаревший.
    # todo вместо этойго метода использовать соответствующий из модуля decart
    # return [Point(- newOriginInOld.x + val.x, - newOriginInOld.y + val.y) for val in pointsInOld]
    result = []
    for value in pointsInOld:
        point = Point()
        point.cardanus = - newOriginInOld.cardanus + value.cardanus
        result.append(point)
    # return [Point(- newOriginInOld.cardanus + val.cardanus) for val in pointsInOld]
    return result