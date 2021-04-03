""" Модуль визуализации происходящего с испытуемым объектом. """
from tkinter import Tk, Canvas, colorchooser, Toplevel, LAST
from queue import Queue
from point import VectorComplex
from stage import Stage, Sizes
from primiteves import AbstractPrimitive, PoligonRectangleA, CenterMassMark, Arrow
from decart import fromOldToNewCoordSystem, pointsListToNewCoordinateSystem
from abc import ABC, abstractmethod
# from torch import tensor
# from cmath import polar
# from itertools import chain
# from physics import BigMap

# from cmath import exp, rect

# X_DIR = 0
# Y_DIR = 1


class PoligonWindow():
    """
    Окно испытательного полигона, на котором рисуется траектория

    """
    class StageMark:
        """
        Метка в виде перекрестия, отображающая положение ступени на полигоне
        """
        def __init__(self, point: VectorComplex, canvas: Canvas):
            # центр масс ступени в СКК
            self.__point = point
            self.__canvas = canvas
            # горизонтальная линия (идентификатор на канве)
            self.__line1 = None
            # вертикальная линия (идентификатор на канве)
            self.__line2 = None

            # длина линии перекрестия
            self.__lineLength = 10

            # если смещение отметки меньше данной величины, то это смещение не отображается
            # двойной размер перекрестия
            self.__trashhold = self.__lineLength

            self.drawMark(self.__point)

        def drawMark(self, point: VectorComplex):
            """
            Рисование отвметки центра масс на канве

            :param point: точка центра масс в СКК
            """
            # горизонтальная линия перекрестия
            self.__line1 = self.__canvas.create_line([point.x - self.__lineLength/2, point.y,
                                                      point.x + self.__lineLength/2, point.y])
            # вертикальная линия перекрестия
            self.__line2 = self.__canvas.create_line([point.x, point.y - self.__lineLength/2,
                                                      point.x, point.y + self.__lineLength/2])

        # def isMarkReady(self):
        #     result = True if self.__line1 is not None and self.__line2 is not None else False
        #     return result

        def moveMark(self, oldPosition: VectorComplex, newPosition: VectorComplex):
            """
            Перемещение перекрестия по канве

            :param oldPosition: старая позиция перекрестия
            :param newPosition: новая позиция перекрестия
            :return: True - если отметка была сдвинута по канве
            :rtype bool:
            """
            # проверка на наличие отметки на канве
            if self.__line1 is None or self.__line2 is None:
                self.drawMark(oldPosition)

            # перемещение отметки в новое место на канве
            delta = newPosition - oldPosition

            if abs(delta.cardanus) < self.__trashhold:
                # Если изменение положения меньше минимального, то движение не отображаем
                return False

            self.__canvas.move(self.__line1, delta.x, delta.y)
            self.__canvas.move(self.__line2, delta.x, delta.y)

            return True

    def __init__(self, frameRate: int, queue: Queue, poligonWidth: float, poligonHeigt: float, poligonScale: float, stageSize: float, stageScale: float):
        """

        :param frameRate: частота кадров (и поступления данных в очередь)
        :param queue: очередь данных для отрисовки траектории в главном окне.
        :param poligonWidth: ширина испытательного полигона (точка посадки находится посередине)
        :param poligonHeigt: высота испытательного полигона (от уровня грунта)
        :param poligonScale: масштаб отображения полигона. Количество метров на одну точку.
        """
        self.__poligonWidth = poligonWidth
        self.__poligonHeigt = poligonHeigt
        # масштаб изображения полигона пикселей на метр
        self.__poligonScale = poligonScale
        # стартовая точка испытаний в СКК
        self.__startPoint = VectorComplex.getInstance(self.__poligonWidth / self.__poligonScale / 2, 5 / self.__poligonScale)
        # реальный размер на масштаб
        # точка посадки в СКК
        self.__endPoint = VectorComplex.getInstance(self.__poligonWidth / self.__poligonScale / 2, 95 / self.__poligonScale)
        # текущая координата ЦМ ступени в СКК
        self.__currentPoint = VectorComplex.getInstance(self.__poligonWidth / self.__poligonScale / 2, 20 / self.__poligonScale)

        self.__frameRate = frameRate
        self.__queue = queue
        # Очередь для передачи данных в дочернее окно
        self.__subQueue = Queue()
        # size = 600
        self.__root = Tk()
        self.__root.geometry("+300+100")
        self.__root.title("Trajectory")
        self.__canvas = Canvas(self.__root, width=self.__poligonWidth / self.__poligonScale, height=self.__poligonHeigt / self.__poligonScale)
        self.__canvas.pack()
        self.__createStaticMarks()
        # Отметка на экране ЦМ ступени в СКК
        self.__stageMark = PoligonWindow.StageMark(VectorComplex.getInstance(25 / self.__poligonScale, 20 / self.__poligonScale), self.__canvas)
        self.__root.after(self.__frameRate, self.__draw)
        # self.__root.mainloop()

        # Окно увеличенного изображения ступени в просессе посадки
        self.__stageWindow = StageViewWindow(self.__root, stageSize, stageScale, frameRate, self.__subQueue)

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
            # сдвинуть отметку ЦМ ступени
            if self.__stageMark.moveMark(self.__currentPoint, transform.vector2d / self.__poligonScale):
                # значение обновляем только тогда, если производился сдвиг отметки по канве
                # в противном случае, прошедшее значение смещения попало в трэшхолд и не является значимым
                self.__currentPoint = transform.vector2d / self.__poligonScale
            # self.__drawMassCenterMark()
            # рисовать
            # self.__stage.draw()
            # двигать
            # self.__stage.move(transform.vector2d)
            # вращать
            # self.__stage.rotate(transform.orientation2d)
            # print(transform.orientation2d.cardanus)
            # print(transform.text)
            # обновляем текущую точку ступени

        # запускаем отрисовку цикл
        self.__root.after(self.__frameRate, self.__draw)

    def __createStaticMarks(self):
        # метод расставляет необходимые отметки по полигону (точка сброса ступени, точка посадки ступени и пр.)
        # отметка точки посадки в виде треугольника
        self.__canvas.create_polygon([self.__endPoint.x - 5, self.__endPoint.y,
                                      self.__endPoint.x, self.__endPoint.y - 5,
                                      self.__endPoint.x + 5, self.__endPoint.y], fill="#1f1")
        # Отметка точки начала спуска ступени
        self.__canvas.create_oval([self.__startPoint.x - 5, self.__startPoint.y - 5,
                                   self.__startPoint.x + 5, self.__startPoint.y + 5],
                                  fill="green")


class StageViewWindow():
    """
    Класс окна вывода увеличенного изображения ступени и числовых характеристик
    """
    def __init__(self, root: Tk, stageSize: float, stageScale: float, frameRate: int, anyQueue: Queue):
        """
        :param root:
        :param stageSize: максимальный размер ступени
        :param stageScale: масштаб изображения ступени на канве
        :param frameRate: частота "кадров" - частота, с которой окно запрашивает данные из очереди
        :param anyQueue: очередь для передачи данных одного фрейма движения ступени
        """
        self.__stageSize = stageSize
        self.__stageScale = stageScale
        self.__anyQueue = anyQueue
        self.__frameRate = frameRate  # частота кадров

        self.__windowWidth = self.__stageSize / self.__stageScale * 2
        self.__windowHeight = self.__stageSize / self.__stageScale * 2 * 4

        # size = 600
        # self.__root = Tk()
        self.__root = Toplevel(root)
        self.__root.title("Stage view")
        self.__canvas = Canvas(self.__root, width=self.__windowWidth, height=self.__windowHeight)
        # canvas.
        # тестовая точка на экране, показывающая ориентацию СКК. Монтажное положение ЦМ в СКК
        test = [Sizes.widthCenterBlock / 2 / 0.25, Sizes.heightCenterBlock * 2/3 / 0.25]
        self.__canvas.create_oval([test[0]-5, test[1]-5, test[0]+5, test[1]+5], fill="red")

        self.__canvas.pack()
        self.__stage = FirstStage2(self.__canvas, self.__stageScale)
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
            self.__stage.move(transform.vector2d / self.__stageScale)
            # вращать
            self.__stage.rotate(transform.orientation2d)
            # print(transform.orientation2d.cardanus)
            # print(transform.text)
        # self.__stage.

        # запускаем отрисовку цикл
        self.__root.after(self.__frameRate, self.__draw)


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
    def __init__(self, canvas: Canvas, scale: float):
        """

        :param canvas: канва
        :param scale: масштаб изображения ступени на канве
        """
        self.__canvas = canvas
        self.__scale = scale
        # Алгоритм сборки.
        # -----
        # Во время графической сборки примитивов, все вектора отсчитываются (для простоты) от левого верхнего угла
        # центрального блока. То есть, левый верхний угол центрального блока находится в начале координат канвы (1).
        #
        # После сборки, координаты ступени пересчитываются в точку координат её центра масс (2)
        #
        # Затем ступень переносится в своё начальное положение (3)
        # -----
        # Установка ракеты в позицию на холсте приозводится за счёт указания вектора центра масс ступени,
        # привязанного к системе координат холста.
        # В данном случае, установка произведена так, чтобы верхний левый угол центрального блока
        # совпал с началом координат канвы
        #
        # центр масс (центр вращения) в системе координат канвы
        self.__massCenter \
            = VectorComplex.getInstance(Sizes.widthCenterBlock / 2 / self.__scale, Sizes.heightCenterBlock * 2/3 / self.__scale)
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

        # массив всех примитивов ступени
        self.__allPrimitives = []

        # отметка центра масс
        # self.__massCenterMark = self.__canvas.create_oval(self.__massCenter.x - 5, self.__massCenter.y - 5,
        #                                                   self.__massCenter.x + 10, self.__massCenter.y + 10,
        #                                                   fill="green")
        self.__massCenterMark = CenterMassMark(self.__canvas, self.__massCenter.x - 2, self.__massCenter.y - 2,
                                                          self.__massCenter.x + 2, self.__massCenter.y + 2,
                                                          fill="green")
        self.__allPrimitives.append(self.__massCenterMark)

        # Корпус ступени.
        # Верхний левый угол ступени находится в начале координат канвы. В этом положении ступень находится до конца
        # сборки всех примитивов
        self.__tank = PoligonRectangleA(self.__canvas).\
            create2points(VectorComplex.getInstance(0., 0.),
                          VectorComplex.getInstance(Sizes.widthCenterBlock / self.__scale, Sizes.heightCenterBlock / self.__scale),
                          self.__massCenter)
        self.__allPrimitives.append(self.__tank)

        # верхний левый маневровый двигатель
        # создание в нулевой позиции
        self.__topLeftJet = PoligonRectangleA(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__topLeftJet.preliminaryMove(VectorComplex.getInstance(- Sizes.widthJet / self.__scale, 0))
        self.__allPrimitives.append(self.__topLeftJet)

        # верхний правый маневровый двигатель
        # создание в нулевой позиции
        self.__topRightJet = PoligonRectangleA(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__topRightJet.preliminaryMove(VectorComplex.getInstance(Sizes.widthCenterBlock / self.__scale, 0))
        self.__allPrimitives.append(self.__topRightJet)

        # нижний левый маневровый двигатель
        # создание в нулевой позиции
        self.__downLeftJet = PoligonRectangleA(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__downLeftJet.preliminaryMove(VectorComplex.getInstance(- Sizes.widthJet / self.__scale, (Sizes.heightCenterBlock - Sizes.heightJet) / self.__scale))
        self.__allPrimitives.append(self.__downLeftJet)

        # нижний правый маневровый двигатель
        # создание в нулевой позиции
        self.__downRightJet = PoligonRectangleA(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__downRightJet.preliminaryMove(VectorComplex.getInstance(Sizes.widthCenterBlock / self.__scale, (Sizes.heightCenterBlock - Sizes.heightJet) / self.__scale))
        self.__allPrimitives.append(self.__downRightJet)

        # маршевый двигатель
        # создание в нулевой позиции
        self.__mainJet = PoligonRectangleA(self.__canvas).\
            create2points(VectorComplex.getInstance(0, 0),
                          VectorComplex.getInstance(Sizes.widthMainJet / self.__scale, Sizes.heightMainJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__mainJet.preliminaryMove(VectorComplex.getInstance((Sizes.widthCenterBlock-Sizes.widthMainJet)/2 / self.__scale, Sizes.heightCenterBlock / self.__scale))
        self.__allPrimitives.append(self.__mainJet)

    def draw(self):
        """
        Рисовать (создать) ступерь на канве. Создаётся единственно только при ПЕРВОМ вызове.
        """
        for primitive in self.__allPrimitives:
            primitive.draw()

    def move(self, newMassCenter: VectorComplex):
        """
        Двигать ступень.

        :param newMassCenter: новые координаты ЦМ в СКК
        """
        # смещение ЦМ в СКК
        # moveVector = VectorComplex.sub(newMassCenter, self.__massCenter)
        moveVector = newMassCenter - self.__massCenter

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


