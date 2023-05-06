""" Модуль интерфейсов блоков приложения: физ. модели, обучения нейросети, визуализации процесса. """
from abc import ABC, abstractmethod

class IAppModule(ABC):
    """ Интерфейс вычислительного блока приложения. """
    @abstractmethod
    def initialization(self) -> None:
        """ Инициализация блока приложения. """
        pass

    @abstractmethod
    def run(self) -> None:
        """ Выполняемый метод блока приложения. """
        pass


class IPhysics(IAppModule):
    """ Интерфейс физического блока приложения. """
    @abstractmethod
    def initialization(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class INeuronet(IAppModule):
    """ Интерфейс блока нейросети приложения. """
    @abstractmethod
    def initialization(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class IVisualization(IAppModule):
    """ Интерфейс блока визуализации приложения. """
    @abstractmethod
    def initialization(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass
