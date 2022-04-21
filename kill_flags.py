class KillNeuroNetThread:
    """ Флаг-команда завершения нити. """
    def __init__(self, kill: bool):
        self.__value = kill

    @property
    def kill(self):
        return self.__value

    @kill.setter
    def kill(self, value: bool):
        self.__value = value


class KillRealWorldThread:
    """ Флаг-команда завершения нити. """
    def __init__(self, kill: bool):
        self.__value = kill

    @property
    def kill(self):
        return self.__value

    @kill.setter
    def kill(self, value: bool):
        self.__value = value