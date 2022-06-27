"""" Модуль крупного изображения изделия """
from point import VectorComplex
from tkinter import Canvas
from stage_fc import AbstractFSFactory, ConcreteFSFactory1


class FirstStage2:
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
    def __init__(self, canvas: Canvas, assembling_point: VectorComplex,
                 mass_center_in_canvas: VectorComplex, linked_marks: list, scale: float):
        """

        :param canvas: канва
        :param assembling_point: точка, относительно которой собираются все примитивы
        :param mass_center_in_canvas: центр масс собранного изделия на канве
        :param linked_marks: список меток привязанных к изображению изделия, метки привязываются к ЦМ изделия
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
        self.__mass_center = mass_center_in_canvas.lazy_copy()

        self.__factory: AbstractFSFactory = ConcreteFSFactory1(canvas, assembling_point, self.__mass_center, scale)
        #
        # Так как при создании ступень стоит вертикально, данный вектор (вектор продольной оси) направлен по оси Y
        # в системе отсчёта канвы
        self.__direction_vector = VectorComplex.get_instance(0., -1.)

        # массив всех примитивов ступени
        self.__all_primitives = [self.__factory.stage_body, self.__factory.top_left_jet, self.__factory.top_right_jet,
                                 self.__factory.down_left_jet, self.__factory.down_right_jet, self.__factory.main_jet]

        # смещение собранного изображения ступени в нужную позицию на канве
        prelimenary_move_vector = VectorComplex.get_instance(50., 50.)
        # создаём копию объекта "координаты центра масс"
        mass_center = mass_center_in_canvas.lazy_copy()
        # смещаем центр масс
        mass_center += prelimenary_move_vector
        for primitive in self.__all_primitives:
            primitive.preliminaryMove(prelimenary_move_vector)
            # все примитивы ступени привязываются к одному объекту "координаты центра масс", как к центру вращения
            primitive.rotationCenter = mass_center

        for mark in linked_marks:
            mark.preliminaryMove(prelimenary_move_vector)
            # все метки, связанные со ступенью, так же привязываются к одному и тому же объекту "координаты центра масс"
            mark.rotationCenter = mass_center

    def create_on_canvas(self):
        """
        Рисовать (создать) ступень на канве. Создаётся один единственный раз только при ПЕРВОМ вызове.
        """
        for primitive in self.__all_primitives:
            primitive.create_on_canvas()

    def move(self, new_mass_center: VectorComplex):
        """
        Двигать ступень.

        :param new_mass_center: новые координаты ЦМ в СКК
        """
        # смещение ЦМ в СКК
        # move_vector = VectorComplex.sub(new_mass_center, self.__mass_center)
        move_vector = new_mass_center - self.__mass_center

        for primitive in self.__all_primitives:
            primitive.move(move_vector)

        self.__mass_center = new_mass_center

    def rotate(self, new_vector: VectorComplex):
        """
        Вращать ступень.

        :param new_vector:
        """
        for primitive in self.__all_primitives:
            primitive.rotate(new_vector, self.__direction_vector)

        # Обновляем значение
        self.__direction_vector = new_vector
