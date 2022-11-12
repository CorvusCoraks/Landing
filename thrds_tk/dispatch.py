""" Модуль диспетчера, реализующего блоки вычислений через нити. """
from ifc_flow.i_disp import IFlowDispatcher
from thrds_tk.physics import PhysicsThread
from thrds_tk.visual import Visualization
from thrds_tk.neuronet import NeuronetThread


class ThreadsDispatcher(IFlowDispatcher):
    def __init__(self):
        self.__visualization: Visualization = Visualization()
        self.__physics: PhysicsThread = PhysicsThread(name="PhysicsThread")
        self.__neuronet: NeuronetThread = NeuronetThread(name="NeuronetThread")

    def initialization(self) -> None:
        pass

    def run(self) -> None:
        self.__physics.initialization()
        # self.__physics.start()
        ...
        self.__neuronet.initialization()
        # self.__neuronet.start()
        ...
        self.__visualization.initialization()
        # Запуск визуализации в главной нити (требование Tkinter)
        self.__visualization.run()
        ...
        # self.__physics.join()
        # self.__neuronet.join()
