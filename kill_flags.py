""" Флаги завершения нитей """


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
        assert (create_key == KillCommandsContainer.__create_key), \
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
