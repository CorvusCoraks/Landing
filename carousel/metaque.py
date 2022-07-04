""" Композиция всех очередей данных в приложении в один класс. """
from carousel.carousel import Carousel
# from carousel.trolleys import RealWorldTrolleyN, CommandTrolleyN
from structures import RealWorldStageStatusN, StageControlCommands, ReinforcementValue


class MetaQueueN:
    """ Класс инкапсулирующий очереди обмена данных в приложении """
    def __init__(self, trolley_quantity: int):
        # state_trolley_quantity = 2
        self.__state_to_neuronet: Carousel = Carousel(RealWorldStageStatusN(time_stamp=-1), trolley_quantity)
        self.__state_to_view: Carousel = Carousel(RealWorldStageStatusN(time_stamp=-1), trolley_quantity)
        self.__state_to_stage_view: Carousel = Carousel(RealWorldStageStatusN(time_stamp=-1), trolley_quantity)
        self.__command_to_real: Carousel = Carousel(StageControlCommands(time_stamp=-1), trolley_quantity)
        self.__reinforcement_to_neuronet: Carousel = Carousel(ReinforcementValue(-1, 0), trolley_quantity)

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