""" Модуль диспетчера, управляющего вычислительными блоками приложения. """
from abc import ABC, abstractmethod
# from i_flow import IAppModule


class IFlowDispatcher(ABC):
    """ Интерфейс диспетчера вычислительных блоков. """

    # def __init__(self, visualization: IAppModule, physics: IAppModule, neuronet: IAppModule):
    #     self.__visualization: IAppModule = visualization
    #     self.__physics: IAppModule = physics
    #     self.__neuronet: IAppModule = neuronet

    @abstractmethod
    def initialization(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass