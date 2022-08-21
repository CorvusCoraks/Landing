""" Флаги завершения нитей """
from abc import ABC, abstractmethod, abstractproperty


class KillCommand:
    """ Базовый класс для флагов завершения нитей. """
    def __init__(self, kill=False):
        """
        :param kill: значение флага
        """
        self.__value = kill

    @property
    def kill(self):
        return self.__value

    @kill.setter
    def kill(self, value: bool):
        self.__value = value


class KillNeuroNetThread(KillCommand):
    """ Флаг завершения нити нейросети. """
    def __init__(self, kill=False):
        KillCommand.__init__(self, kill)


class KillRealWorldThread(KillCommand):
    """ Флаг завершения нити реального физического мира. """
    def __init__(self, kill=False):
        KillCommand.__init__(self, kill)


class KillCommandsContainer:
    """ В этом классе скомпонованы флаги-команды на завершения работы нитей. Синглтон """
    # ссылка на объект Синглтон
    __this_object: 'KillCommandsContainer' = None
    # ключ для закрытия метода __init__
    __create_key = object()

    def __init__(self, create_key):
        assert (create_key is KillCommandsContainer.__create_key), \
            "KillCommands object must be created using get_instanse method."

        self.__killNeuroNetThread: KillNeuroNetThread = KillNeuroNetThread()
        self.__killRealityThread: KillRealWorldThread = KillRealWorldThread()

    @classmethod
    def get_instance(cls) -> 'KillCommandsContainer':
        """ Возвращает объект типа KillCommandContainer. Если он не существует, то предварительно создаёт его. """
        if KillCommandsContainer.__this_object is None:
            KillCommandsContainer.__this_object = KillCommandsContainer(KillCommandsContainer.__create_key)

        return KillCommandsContainer.__this_object

    @property
    def neuro(self) -> bool:
        return self.__killNeuroNetThread.kill

    @neuro.setter
    def neuro(self, value: bool):
        self.__killNeuroNetThread.kill = value

    @property
    def reality(self) -> bool:
        return self.__killRealityThread.kill

    @reality.setter
    def reality(self, value: bool):
        self.__killRealityThread.kill = value


class KillInterface(ABC):
    """ Абстрактный интерфейс для считывания и установки команды завершения нити. """
    @property
    @abstractmethod
    def kill(self) -> bool:
        pass

    @kill.setter
    @abstractmethod
    def kill(self, value: bool) -> None:
        pass


class RealityKillInterface(KillInterface):
    """ Абстрактный интерфейс для установки и считывания команды завершения нити реальности. """
    def __init__(self):
        super().__init__()

    @property
    @abstractmethod
    def kill(self) -> bool:
        pass

    @kill.setter
    @abstractmethod
    def kill(self, value: bool) -> None:
        pass


class NeuroKillInterface(KillInterface):
    """ Абстрактный интерфейс для установки и считывания команды завершения нити нейросети. """
    def __init__(self):
        super().__init__()

    @property
    @abstractmethod
    def kill(self) -> bool:
        pass

    @kill.setter
    @abstractmethod
    def kill(self, value: bool) -> None:
        pass


# class MainThreadKillInterface(KillInterface):
#     def __init__(self):
#         super().__init__()
#
#     @property
#     @abstractmethod
#     def kill_neuro(self) -> bool:
#         pass
#
#     @kill_neuro.setter
#     @abstractmethod
#     def kill_neuro(self, valuet: bool) -> None:
#         pass


class KillCommandsContainerN:
    """ В этом классе скомпонованы флаги-команды на завершения работы нитей. Синглтон """
    # ссылка на объект Синглтон
    __this_object: 'KillCommandsContainerN' = None
    # ключ для закрытия метода __init__
    __create_key = object()

    class Reality(RealityKillInterface):
        """ Класс-интерфейс для работы с командами завершения нити реальности. """
        def __init__(self, container: 'KillCommandsContainerN'):
            super().__init__()

            self.__container = container

        @property
        def kill(self) -> bool:
            return self.__container.i_reality

        @kill.setter
        def kill(self, value: bool) -> None:
            self.__container.i_reality = value

    class Neuro(NeuroKillInterface):
        """ Класс-интерфейс для работы с командами завершения нити нейросети. """
        def __init__(self, container: 'KillCommandsContainerN'):
            super().__init__()

            self.__container = container

        @property
        def kill(self) -> bool:
            return self.__container.i_neuro

        @kill.setter
        def kill(self, value: bool) -> None:
            self.__container.i_neuro = value

        # class MainThread(MainThreadKillInterface):
        #     def __init__(self, container: 'KillCommandsContainerN'):
        #         super().__init__()
        #
        #         self.__container = container
        #
        #     @property
        #     def kill_neuro(self) -> bool:
        #         # Главная нить останавливается не через эти флаги, а другими способами.
        #         return False
        #
        #     @kill_neuro.setter
        #     def kill_neuro(self, value: bool) -> None:
        #         # Главная нить останавливается не через эти флаги, а другими способами.
        #         self.__container.i_neuro = False

    def __init__(self, create_key):
        assert (create_key is KillCommandsContainerN.__create_key), \
            "KillCommands object must be created using get_instanse method."

        self.__killNeuroNetThread: KillNeuroNetThread = KillNeuroNetThread()
        self.__killRealityThread: KillRealWorldThread = KillRealWorldThread()

        self.__reality_interface = KillCommandsContainerN.Reality(self)
        self.__neuro_interface = KillCommandsContainerN.Neuro(self)

    @classmethod
    def get_instance(cls) -> 'KillCommandsContainerN':
        """ Возвращает объект типа KillCommandContainer. Если он не существует, то предварительно создаёт его. """
        if cls.__this_object is None:
            cls.__this_object = KillCommandsContainerN(cls.__create_key)

        return cls.__this_object

    @property
    def i_neuro(self) -> bool:
        return self.__killNeuroNetThread.kill

    @i_neuro.setter
    def i_neuro(self, value: bool):
        self.__killNeuroNetThread.kill = value

    @property
    def i_reality(self) -> bool:
        return self.__killRealityThread.kill

    @i_reality.setter
    def i_reality(self, value: bool):
        self.__killRealityThread.kill = value

    @property
    def reality(self) -> RealityKillInterface:
        return self.__reality_interface

    @property
    def neuro(self) -> NeuroKillInterface:
        return self.__neuro_interface