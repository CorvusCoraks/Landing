# Интерфейсы визуального представления
from queue import Queue
from kill_flags import KillNeuroNetThread, KillRealWorldThread
from abc import ABC, abstractmethod
from point import VectorComplex
from tkinter import Tk, Canvas, Toplevel
from win import PoligonWindow, StageViewWindow
from win_stageview import InfoView
from stage import Sizes
from typing import Dict, AnyStr, Union
from primiteves import ArcArrowAndText, LineArrowAndText


class ViewInterface(ABC):
    """ AbstractFactory """
    # примитивы, отображающие что-либо конкретно, описываются в конкретной фабрике.
    @abstractmethod
    def set_poligon_state(self, queue: Queue, poligon_width: float, poligon_height: float):
        """ Описание испытательного полигона в СКИП """
        pass

    @abstractmethod
    def set_kill_threads(self, kill_reality: KillRealWorldThread, kill_neuronet: KillNeuroNetThread):
        """ Управляющие команды на удаление нитей """
        pass

    @abstractmethod
    def set_stage_parameters(self, top_mass_from_mc: VectorComplex,
                             down_mass_from_mc: VectorComplex,
                             mc_from_bottom: VectorComplex,
                             stage_width: float, stage_height: float, leg_plane_from_mc: float):
        """ Геометрические параметры изделия. """
        pass

    @abstractmethod
    def create_poligon_view(self):
        """ Создать отображение испытательного полигона. """
        pass

    @abstractmethod
    def create_stage_view(self):
        """ Создать увеличенное отображение изделия. """
        pass

    @abstractmethod
    def create_info_view(self):
        """ Создать отображение информации о параметрах движения изделия. """
        pass




class WindowsMSView(ViewInterface):
    """ ConcreteFactory """
    #
    # todo Класс перенести в отдельный модуль
    #
    def __init__(self):
        self.__env_to_poligon_queue: Queue = Queue()
        self.__env_to_stage_queue: Queue = Queue()
        self.__env_to_info_queue: Queue = Queue()
        pass

    def set_poligon_state(self, queue: Queue, poligon_width: float, poligon_height: float):

        self.__env_to_poligon_queue = queue
        self.__poligon_width = poligon_width
        self.__poligon_height = poligon_height

    def set_kill_threads(self, kill_reality: KillRealWorldThread, kill_neuronet: KillNeuroNetThread):

        self.__kill_reality_thread = kill_reality
        self.__kill_neuronet_thread = kill_neuronet

    # todo перевести просто в линейные размеры на входе? На фиг вектора?
    def set_stage_parameters(self, top_mass_from_mc: float, down_mass_from_mc: float,
                             mc_from_bottom: float, stage_width: float, stage_height: float,
                             leg_plane_from_mc: float):

        self.__top_mass_from_mc = top_mass_from_mc
        self.__down_mass_from_mc = down_mass_from_mc
        self.__mc_from_bottom = mc_from_bottom
        self.__stage_width = stage_width
        self.__stage_height = stage_height
        self.__leg_plane_from_mc = leg_plane_from_mc

    def create_poligon_view(self):

        self.__poligon_scale = 1.
        stage_view_scale = 0.1
        self.__poligon_window = PoligonWindow(-1, self.__env_to_poligon_queue, self.__env_to_stage_queue,
                                      self.__poligon_width, self.__poligon_height,
                                      self.__poligon_scale, Sizes.overallDimension, stage_view_scale,
                                      self.__kill_neuronet_thread, self.__kill_reality_thread)

    def create_stage_view(self):
        stage_view_scale = 0.1

        self.__stage_window = StageViewWindow(self.__poligon_window.root, Canvas(),  Sizes.overallDimension, stage_view_scale, -1,
                                              self.__env_to_stage_queue, self.__env_to_info_queue)

    def create_info_view(self):
        block = InfoView.get_info_block(self.__stage_window.canvas)
        self.__stage_window.create_info_block_on_canvas(block)
        self.__stage_window.root.mainloop()