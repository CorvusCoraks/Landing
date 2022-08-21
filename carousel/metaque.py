""" Композиция всех очередей данных в приложении в один класс. """
from carousel.carousel import Carousel, CarouselB, VoidContaners, Porter, PostOffice
# from carousel.trolleys import RealWorldTrolleyN, CommandTrolleyN
from structures import RealWorldStageStatusN, StageControlCommands, ReinforcementValue, StageState, ControlCommands, BatchSizeMessage, ReinforcementMessage
from typing import Any, Optional
from kill_flags import KillInterface, KillCommandsContainerN


class MetaQueueN:
    """ Класс инкапсулирующий очереди обмена данных в приложении """
    def __init__(self, trolley_quantity: int):
        # state_trolley_quantity = 2
        self.__state_to_neuronet: Carousel = Carousel(RealWorldStageStatusN(time_stamp=-1), trolley_quantity)
        self.__state_to_view: Carousel = Carousel(RealWorldStageStatusN(time_stamp=-1), trolley_quantity)
        self.__state_to_stage_view: Carousel = Carousel(RealWorldStageStatusN(time_stamp=-1), trolley_quantity)
        self.__command_to_real: Carousel = Carousel(StageControlCommands(time_stamp=-1), trolley_quantity)
        self.__reinforcement_to_neuronet: Carousel = Carousel(ReinforcementValue(time_stamp=-1, reinforcement=0.), trolley_quantity)

    @property
    def state_to_neuronet(self) -> Carousel:
        return self.__state_to_neuronet

    @property
    def state_to_view(self) -> Carousel:
        return self.__state_to_view

    @property
    def state_to_stage_view(self) -> Carousel:
        return self.__state_to_stage_view

    @property
    def command_to_real(self) -> Carousel:
        return self.__command_to_real

    @property
    def reinf_to_neuronet(self):
        return self.__reinforcement_to_neuronet


class Channal:
    """ Двунаправленный канал передачи данных """
    def __init__(self, trolley_quantity: int, listener_kill: Optional[KillInterface], *args: Any):
        """

        :param trolley_quantity: Начальное количество вагонеток канала.
        :param listener_kill: Флаг команды на закрытие нити ПОЛУЧАТЕЛЯ данных
        :param args: Кортеж объектов-прототипов контейнеров, циркулирующих по каналу
        """
        self.__carousel: CarouselB = CarouselB(trolley_quantity)
        self.__store: VoidContaners = VoidContaners(*args)
        self.__porter: Porter = Porter(self.__store)
        self.__post_office: PostOffice = PostOffice(self.__carousel, self.__porter)

    @property
    def queue(self) -> PostOffice:
        return self.__post_office


class MetaQueue2:
    """ Класс инкапсулирующий очереди обмена данных в приложении. Singletone. """

    # Ссылка на объект Singletone
    __this_object: Optional['MetaQueue2'] = None
    # ключ синглтона
    __create_key: object = object()

    def __init__(self, create_key: object, kill: KillCommandsContainerN):
        assert (create_key is MetaQueue2.__create_key), \
            "MetaQueue2 object must be created using get_instance method."

        self.__state_to_neuronet: Channal = Channal(10, kill.neuro, StageState(), BatchSizeMessage())
        self.__state_to_view: Channal = Channal(10, kill.reality, StageState())
        self.__state_to_stage_view: Channal = Channal(10, kill.reality, StageState())
        self.__command_to_real: Channal = Channal(10, kill.reality, ControlCommands())
        self.__reinforcement_to_neuronet: Channal = Channal(10, kill.neuro, ReinforcementMessage())

    @classmethod
    def get_instance(cls, kill: KillCommandsContainerN):
        if cls.__this_object is None:
            cls.__this_object = MetaQueue2(cls.__create_key, kill)
        return cls.__this_object

    @property
    def state_to_neuronet(self) -> PostOffice:
        return self.__state_to_neuronet.queue

    @property
    def state_to_view(self) -> PostOffice:
        return self.__state_to_view.queue

    @property
    def state_to_stage_view(self) -> PostOffice:
        return self.__state_to_stage_view.queue

    @property
    def command_to_real(self) -> PostOffice:
        return self.__command_to_real.queue

    @property
    def reinf_to_neuronet(self) -> PostOffice:
        return self.__reinforcement_to_neuronet.queue