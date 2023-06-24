""" Интерфейс окна MS Windows """
from abc import ABC, abstractmethod

# WindowsMSInterface -> PoligonWindow
#           └-> StageViewWindow

class WindowsMSInterface(ABC):
    """ Интерфейс окна в Windows при использовании Tkinter и Canvas """
    # todo веменное расположение в этом модуле, так как запутанные и конфликтующие импорты
    @abstractmethod
    def _draw(self, *args):
        """ метод для периодической перерисовки объектов на канве """
        pass

    @abstractmethod
    def _preparation_static_marks(self):
        """ Подготовка статичных меток или объектов """
        pass

    @abstractmethod
    def _preparation_movable_marks(self):
        """ Подготовка подвижных (линенейно или вращающихся) меток или объектов """
        pass

    @abstractmethod
    def _create_objects_on_canvas(self):
        """ Создание на канве и подвижных, и неподвижных элементов """
        pass

    @abstractmethod
    def root(self):
        pass

    @abstractmethod
    def canvas(self):
        pass