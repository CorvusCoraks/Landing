""" Модуль нитей моделирования физического мира """
from datadisp.adisp import DispatcherAbstract
from datadisp.listdisp import ListDispatcher
from carousel.metaque import MetaQueueN
from kill_flags import KillCommandsContainer
from carousel.carousel import Carousel
# from carousel.trolleys import RealWorldTrolleyN


# ThreadType = TypeVar('ThreadType', bound='PrototypeInterface')

# def reality_thread(dispatcher: DispatcherAbstract):
#     """ Функция нити реальности. """
#     # dispatcher: DispatcherAbstract = ListDispatcher(meta_queue, batch_size, kill_neuro)
#     print("Вход в нить окружающей среды.")
#     dispatcher.run()
#     print("Завершение нити реальности.")


# if __name__ == '__main__':
#     # c = Carousel(RealWorldTrolley(), 2)
#     dispatcher = ListDispatcher(MetaQueueN(), 2, KillCommandsContainer.get_instance())
#     reality_thread(dispatcher)




