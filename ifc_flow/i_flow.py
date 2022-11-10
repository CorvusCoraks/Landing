from abc import ABC, abstractmethod

class IAppModule(ABC):
    """ Интерфейс вычислительного модуля приложения. """
    @abstractmethod
    def initialization(self):
        """ Инициализация блока приложения. """
        pass

    @abstractmethod
    def run(self):
        """ Выполняемый метод блока приложения. """
        pass


class IPhysics(IAppModule):
    """ Интерфейс физического модуля приложения. """
    @abstractmethod
    def initialization(self):
        pass

    @abstractmethod
    def run(self):
        pass


class INeuronet(IAppModule):
    """ Интерфейс модуля нейросети приложения. """
    @abstractmethod
    def initialization(self):
        pass

    @abstractmethod
    def run(self):
        pass


class IVisualization(IAppModule):
    """ Интерфейс модуля визуализации приложения. """
    @abstractmethod
    def initialization(self):
        pass

    @abstractmethod
    def run(self):
        pass
