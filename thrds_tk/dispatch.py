""" Модуль диспетчера, реализующего блоки вычислений через нити. """
from ifc_flow.i_disp import IFlowDispatcher
from ifc_flow.i_flow import IAppModule
from thrds_tk.physics import PhysicsThread
from thrds_tk.visual import VisualThread
from thrds_tk.neuronet import NeuronetThread
from threading import Thread


class ThreadsDispatcher(IFlowDispatcher):
    def __init__(self):
        self.__visualization: IAppModule = VisualThread()
        self.__physics: IAppModule = PhysicsThread()
        self.__neuronet: IAppModule = NeuronetThread()

    def initialization(self):
        pass

    def run(self):
        self.__physics.initialization()
        ...
        self.__neuronet.initialization()
        ...
        self.__visualization.initialization()
