from abc import ABC, abstractmethod

class IAppModule(ABC):
    """ Интерфейс вычислительного модуля приложения. """
    @abstractmethod
    def initialization(self) -> None:
        """ Инициализация блока приложения. """
        pass

    @abstractmethod
    def run(self) -> None:
        """ Выполняемый метод блока приложения. """
        pass


class IPhysics(IAppModule):
    """ Интерфейс физического модуля приложения. """
    @abstractmethod
    def initialization(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class INeuronet(IAppModule):
    """ Интерфейс модуля нейросети приложения. """
    @abstractmethod
    def initialization(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class IVisualization(IAppModule):
    """ Интерфейс модуля визуализации приложения. """
    @abstractmethod
    def initialization(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass
