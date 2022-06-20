"""" Модуль крупного изображения изделия """
from point import VectorComplex
from primiteves import PoligonRectangleA
from tkinter import Canvas
from stage import Sizes

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
    def __init__(self, canvas: Canvas, assemblingPoint: VectorComplex, massCenterInCanvas: VectorComplex, linkedMarks: list, scale: float):
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
        # self.__massCenter \
        #     = VectorComplex.get_instance(Sizes.widthCenterBlock / 2 / self.__scale, Sizes.heightCenterBlock * 2/3 / self.__scale)
        self.__massCenter = massCenterInCanvas.lazy_copy()
        #
        # Так как при создании ступень стоит вертикально, данный вектор (вектор продольной оси) направлен по оси Y
        # в системе отсчёта канвы
        # self.__directionVector = Point(0., 1.)
        # todo возможно (0, -1)?
        self.__directionVector = VectorComplex.get_instance(0., -1.)

        # Все примитивы изначально рисуются в привязке к началу координат канвы, с целью упрощения задания координат
        # ключевых точек.
        # В последствии, при не обходимости, примитивы перемещаются в нужное положение целиком.

        # массив всех примитивов ступени
        self.__allPrimitives = []

        # # отметка центра масс
        # self.__massCenterMark = CenterMassMark(self.__canvas, VectorComplex.get_instance(self.__massCenter.x - 2, self.__massCenter.y - 2),
        #                                                   VectorComplex.get_instance(self.__massCenter.x + 2, self.__massCenter.y + 2),
        #                                        self.__massCenter,
        #                                                   fill="green")
        # self.__allPrimitives.append(self.__massCenterMark)

        # Корпус ступени.
        # Верхний левый угол ступени находится в начале координат канвы. В этом положении ступень находится до конца
        # сборки всех примитивов
        self.__tank = PoligonRectangleA(self.__canvas).\
            create2points(assemblingPoint + VectorComplex.get_instance(0., 0.),
                          assemblingPoint + VectorComplex.get_instance(Sizes.widthCenterBlock / self.__scale, Sizes.heightCenterBlock / self.__scale),
                          self.__massCenter)
        self.__allPrimitives.append(self.__tank)

        # верхний левый маневровый двигатель
        # создание в нулевой позиции
        self.__topLeftJet = PoligonRectangleA(self.__canvas).\
            create2points(assemblingPoint + VectorComplex.get_instance(0, 0),
                          assemblingPoint + VectorComplex.get_instance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__topLeftJet.preliminaryMove(assemblingPoint + VectorComplex.get_instance(- Sizes.widthJet / self.__scale, 0))
        self.__allPrimitives.append(self.__topLeftJet)

        # верхний правый маневровый двигатель
        # создание в нулевой позиции
        self.__topRightJet = PoligonRectangleA(self.__canvas).\
            create2points(assemblingPoint + VectorComplex.get_instance(0, 0),
                          assemblingPoint + VectorComplex.get_instance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__topRightJet.preliminaryMove(assemblingPoint + VectorComplex.get_instance(Sizes.widthCenterBlock / self.__scale, 0))
        self.__allPrimitives.append(self.__topRightJet)

        # нижний левый маневровый двигатель
        # создание в нулевой позиции
        self.__downLeftJet = PoligonRectangleA(self.__canvas).\
            create2points(assemblingPoint + VectorComplex.get_instance(0, 0),
                          assemblingPoint + VectorComplex.get_instance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__downLeftJet.preliminaryMove(assemblingPoint + VectorComplex.get_instance(- Sizes.widthJet / self.__scale, (Sizes.heightCenterBlock - Sizes.heightJet) / self.__scale))
        self.__allPrimitives.append(self.__downLeftJet)

        # нижний правый маневровый двигатель
        # создание в нулевой позиции
        self.__downRightJet = PoligonRectangleA(self.__canvas).\
            create2points(assemblingPoint + VectorComplex.get_instance(0, 0),
                          assemblingPoint + VectorComplex.get_instance(Sizes.widthJet / self.__scale, Sizes.heightJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__downRightJet.preliminaryMove(assemblingPoint + VectorComplex.get_instance(Sizes.widthCenterBlock / self.__scale, (Sizes.heightCenterBlock - Sizes.heightJet) / self.__scale))
        self.__allPrimitives.append(self.__downRightJet)

        # маршевый двигатель
        # создание в нулевой позиции
        self.__mainJet = PoligonRectangleA(self.__canvas).\
            create2points(assemblingPoint + VectorComplex.get_instance(0, 0),
                          assemblingPoint + VectorComplex.get_instance(Sizes.widthMainJet / self.__scale, Sizes.heightMainJet / self.__scale),
                          self.__massCenter)
        # смещение примитива в монтажную позицию
        self.__mainJet.preliminaryMove(assemblingPoint + VectorComplex.get_instance((Sizes.widthCenterBlock - Sizes.widthMainJet) / 2 / self.__scale, Sizes.heightCenterBlock / self.__scale))
        self.__allPrimitives.append(self.__mainJet)

        # смещение собранного изображения ступени в нужную позицию на канве
        prelimenaryMoveVector = VectorComplex.get_instance(50., 50.)
        # создаём копию объекта "координаты центра масс"
        massCenter = massCenterInCanvas.lazy_copy()
        # смещаем центр масс
        massCenter += prelimenaryMoveVector
        for primitive in self.__allPrimitives:
            primitive.preliminaryMove(prelimenaryMoveVector)
            # все примитивы ступени привязываются к одному объекту "координаты центра масс", как к центру вращения
            primitive.rotationCenter = massCenter

        for mark in linkedMarks:
            mark.preliminaryMove(prelimenaryMoveVector)
            # все метки, связанные со ступенью, так же привязываются к одному и тому же объекту "координаты центра масс"
            mark.rotationCenter = massCenter

    def createOnCanvas(self):
        """
        Рисовать (создать) ступень на канве. Создаётся один единственный раз только при ПЕРВОМ вызове.
        """
        for primitive in self.__allPrimitives:
            primitive.createOnCanvas()

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