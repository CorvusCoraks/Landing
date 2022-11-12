""" Модуль, инкапсулирующий стандартный класс *Thread* (Фасад?)"""
from abc import ABC, abstractmethod
from threading import Thread
from time import sleep


class AYarn(ABC):
    """ Класс, инкапсулирующий нить класса *Thread*. """
    @abstractmethod
    def _yarn_run(self, *args, **kwargs) -> None:
        """ Аналог метода *run()* класса *Thread*. Исполняется в нити. Переопределяется в потомках. """
        pass

    def __init__(self, name: str, *args, **kwargs):
        """

        :param name: Имя нити.
        :param args: Позиционные аргументы для метода _yarn_run() исполняемого в нити
        :param kwargs: Именованные аргументы для метода _yarn_run() исполняемого в нити
        """
        self._yarn: Thread = Thread(target=self._yarn_run, name=name, args=args, kwargs=kwargs)

    def start(self):
        """ Обёрнутый вызов метода *start()* класса *Thread* """
        self._yarn.start()

    def join(self):
        """ Обёрнутый вызов метода *join()* класса *Thread* """
        self._yarn.join()


class TestClass(AYarn):
    """ Тестовый класс, для проверки работы потомка класса *AYarn* """
    def __init__(self, any_arg: int, name="NewThread"):
        super().__init__(name, "arg1", "arg2", arg3="arg_3", arg4="arg_4")
        self.__any_arg = any_arg

    def _yarn_run(self, *args, **kwargs) -> None:
        for a in range(3):
            print("Функция внутри нити.\n")
            print(args)
            print(kwargs)
            sleep(1)


if __name__ == "__main__":
    # Тестирование работы потомка класса AYarn
    thread = TestClass(5, name="SubTestThread")
    thread.start()
    thread.join()
