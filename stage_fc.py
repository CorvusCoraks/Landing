""" Фабрика примитивов, составляющих изображение изделия. """
from abc import ABC, abstractmethod
from primiteves import AbstractPrimitive, PoligonRectangleA
from tkinter import Canvas
from point import VectorComplex
from stage import Sizes

class AbstractFSFactory(ABC):
    """ Абстрактная фабрика сборки изображения первой ступени из геометрических примитивов. """
    @property
    @abstractmethod
    def top_left_jet(self) -> AbstractPrimitive:
        """ Изображение левого верхнего двигателя. """
        pass

    @property
    @abstractmethod
    def top_right_jet(self) -> AbstractPrimitive:
        """ Изображение правого верхнего двигателя. """
        pass

    @property
    @abstractmethod
    def down_left_jet(self) -> AbstractPrimitive:
        """ Изображение левого нижнего двигателя. """
        pass

    @property
    @abstractmethod
    def down_right_jet(self) -> AbstractPrimitive:
        """ Изображение нижнего правого двигателя. """
        pass

    @property
    @abstractmethod
    def main_jet(self) -> AbstractPrimitive:
        """ Изображение маршевого двигателя. """
        pass

    @property
    @abstractmethod
    def stage_body(self) -> AbstractPrimitive:
        """ Изображение центрального блока. """
        pass


class ConcreteFSFactory1(AbstractFSFactory):
    """ Конкретная фабрика сборки изображения первой ступени из примитивов №1 """

    # Все примитивы изначально рисуются в привязке к точке первоначальной сборки, с целью упрощения задания координат
    # ключевых точек. Этой точкой, для простоты может быть начало координат канвы.
    # В последствии, при необходимости, примитивы перемещаются в нужное место, согласно привязке к модели.
    def __init__(self, canvas: Canvas, assempling_point: VectorComplex, mass_center: VectorComplex, scale: float):
        """

        :param canvas: канва tkinter
        :param assempling_point: точка первоначальной отрисовки
        :param mass_center: центр масс всего собранного изделия
        :param scale: масштаб изображения.
        """
        self.__canvas = canvas
        self.__assembling_point = assempling_point
        self.__mass_center = mass_center
        self.__scale = scale

    @property
    def top_left_jet(self):
        # создание в нулевой позиции
        self.__top_left_jet = PoligonRectangleA(self.__canvas). \
            create2points(self.__assembling_point + VectorComplex.get_instance(0, 0),
                          self.__assembling_point + VectorComplex.get_instance(Sizes.widthJet / self.__scale,
                                                                               Sizes.heightJet / self.__scale),
                          self.__mass_center)
        # смещение примитива в монтажную позицию
        self.__top_left_jet.preliminaryMove(
            self.__assembling_point + VectorComplex.get_instance(- Sizes.widthJet / self.__scale, 0))

        return self.__top_left_jet

    @property
    def top_right_jet(self):
        # создание в нулевой позиции
        self.__top_right_jet = PoligonRectangleA(self.__canvas). \
            create2points(self.__assembling_point + VectorComplex.get_instance(0, 0),
                          self.__assembling_point + VectorComplex.get_instance(Sizes.widthJet / self.__scale,
                                                                        Sizes.heightJet / self.__scale),
                          self.__mass_center)
        # смещение примитива в монтажную позицию
        self.__top_right_jet.preliminaryMove(
            self.__assembling_point + VectorComplex.get_instance(Sizes.widthCenterBlock / self.__scale, 0))

        return self.__top_right_jet

    @property
    def down_left_jet(self):
        # создание в нулевой позиции
        self.__down_left_jet = PoligonRectangleA(self.__canvas). \
            create2points(self.__assembling_point + VectorComplex.get_instance(0, 0),
                          self.__assembling_point + VectorComplex.get_instance(Sizes.widthJet / self.__scale,
                                                                        Sizes.heightJet / self.__scale),
                          self.__mass_center)
        # смещение примитива в монтажную позицию
        self.__down_left_jet.preliminaryMove(
            self.__assembling_point + VectorComplex.get_instance(- Sizes.widthJet / self.__scale,
                                                          (Sizes.heightCenterBlock - Sizes.heightJet) / self.__scale))

        return self.__down_left_jet

    @property
    def down_right_jet(self):
        # создание в нулевой позиции
        self.__down_right_jet = PoligonRectangleA(self.__canvas). \
            create2points(self.__assembling_point + VectorComplex.get_instance(0, 0),
                          self.__assembling_point + VectorComplex.get_instance(Sizes.widthJet / self.__scale,
                                                                        Sizes.heightJet / self.__scale),
                          self.__mass_center)
        # смещение примитива в монтажную позицию
        self.__down_right_jet.preliminaryMove(
            self.__assembling_point + VectorComplex.get_instance(Sizes.widthCenterBlock / self.__scale,
                                                          (Sizes.heightCenterBlock - Sizes.heightJet) / self.__scale))

        return self.__down_right_jet

    @property
    def main_jet(self):
        # создание в нулевой позиции
        self.__main_jet = PoligonRectangleA(self.__canvas). \
            create2points(self.__assembling_point + VectorComplex.get_instance(0, 0),
                          self.__assembling_point + VectorComplex.get_instance(Sizes.widthMainJet / self.__scale,
                                                                        Sizes.heightMainJet / self.__scale),
                          self.__mass_center)
        # смещение примитива в монтажную позицию
        self.__main_jet.preliminaryMove(self.__assembling_point + VectorComplex.get_instance(
            (Sizes.widthCenterBlock - Sizes.widthMainJet) / 2 / self.__scale, Sizes.heightCenterBlock / self.__scale))

        return self.__main_jet

    @property
    def stage_body(self):
        self.__tank = PoligonRectangleA(self.__canvas). \
            create2points(self.__assembling_point + VectorComplex.get_instance(0., 0.),
                          self.__assembling_point + VectorComplex.get_instance(Sizes.widthCenterBlock / self.__scale,
                                                                        Sizes.heightCenterBlock / self.__scale),
                          self.__mass_center)

        return self.__tank