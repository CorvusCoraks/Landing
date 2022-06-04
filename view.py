# Интерфейсы визуального представления
from queue import Queue
from kill_flags import KillNeuroNetThread, KillRealWorldThread, KillCommandsContainer
from abc import ABC, abstractmethod
from point import VectorComplex
from tools import MetaQueue

# ViewInterface (Abstract Factory) -> AnotherView (Concrete Factory)
#           └-> WindowsMSView (Concrete Factory)

class ViewInterface(ABC):
    """ AbstractFactory """
    # примитивы, отображающие что-либо конкретно, описываются в конкретной фабрике.
    @abstractmethod
    def set_poligon_state(self, queues: MetaQueue, poligon_width: float, poligon_height: float):
        """ Описание испытательного полигона в СКИП """
        pass

    @abstractmethod
    def set_kill_threads(self, kill: KillCommandsContainer):
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
