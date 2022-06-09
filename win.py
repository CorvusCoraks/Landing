""" Модуль реализации абстрактной фабрики визуального представления в MS Windows """
from view import ViewInterface
from queue import Queue
from kill_flags import KillNeuroNetThread, KillRealWorldThread, KillCommandsContainer
from win_testing_area import PoligonWindow
from win_stageview import StageViewWindow, InfoView
from stage import Sizes
from tkinter import Canvas
from tools import MetaQueue

class WindowsMSView(ViewInterface):
    """ ConcreteFactory """

    def __init__(self):
        pass

    def set_poligon_state(self, queues: MetaQueue, poligon_width: float, poligon_height: float):

        self.__queues = queues
        # self.__env_to_poligon_queue = queues.get_queue("area")
        self.__poligon_width = poligon_width
        self.__poligon_height = poligon_height

    def set_kill_threads(self, kill: KillCommandsContainer):

        self.__kill = kill
        # self.__kill_reality_thread = kill_reality
        # self.__kill_neuronet_thread = kill_neuronet

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
        # stage_view_scale = 0.1
        self.__poligon_window = PoligonWindow(self.__queues,
                                      self.__poligon_width, self.__poligon_height,
                                      self.__poligon_scale,
                                      self.__kill)

    def create_stage_view(self):
        stage_view_scale = 0.1

        # self.__stage_window = StageViewWindow(self.__poligon_window.root, Canvas(),  Sizes.overallDimension, stage_view_scale, -1,
        #                                       self.__env_to_stage_queue, self.__env_to_info_queue)
        self.__stage_window = StageViewWindow(self.__poligon_window.root, Sizes.overallDimension, stage_view_scale,
                                              self.__queues)

    def create_info_view(self):
        block = InfoView.get_info_block(self.__stage_window.canvas)
        self.__stage_window.create_info_block_on_canvas(block)
        self.__stage_window.root.mainloop()