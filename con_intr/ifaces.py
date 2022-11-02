""" ISwitchboard - интерфейс объекта очередей сообщений приложения. """
from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, TypeVar


# Тип данных, передаваемых между функциональными блоками приложения.
TransferredData = TypeVar('TransferredData', int, str)


class AppModulesEnum(Enum):
    """ Константы, определяющие функциональные блоки приложения. """
    MAIN = 0
    VIEW = 1
    PHYSICS = 2
    NEURO = 3


class DataTypeEnum(Enum):
    """ Константы, определяющие тип передаваемых данных. """
    REMANING_TESTS = 0
    STAGE_STATUS = 1


class ISender(ABC):
    """ Интерфейс отправителя данных. """
    @abstractmethod
    def send(self, cargo: TransferredData) -> None:
        """ Отправить данные, ожидающие отправления. """
        pass

    @abstractmethod
    def has_outgoing(self) -> bool:
        """ Имеются ли данные для отправления? """
        pass

    @abstractmethod
    def set_receiver(self, receiver: AppModulesEnum) -> None:
        """ Установить получателя данных. """
        pass

    @abstractmethod
    def set_sending_type(self, data_type: DataTypeEnum) -> None:
        """ Установить тип отправляемых данных. """
        pass


class IReceiver(ABC):
    """ Интерфейс получателя данных """
    @abstractmethod
    def receive(self) -> TransferredData:
        """ Получить ожидающие данные. """
        pass

    @abstractmethod
    def has_incoming(self) -> bool:
        """ Имеются ли входящие данные? """
        pass

    @abstractmethod
    def get_sender(self) -> AppModulesEnum:
        """ Кто отправитель? """
        pass

    @abstractmethod
    def get_receiving_type(self) -> DataTypeEnum:
        """ Какой тип данных? """
        pass


class IWire(ABC, ISender, IReceiver):
    """ Интефейс канала передачи данных. """
    # Подразумевает множественные варианты конкретной реализации.
    pass


class ISwitchboard(ABC):
    """ Интерфейс класса объединяющего все каналы передачи данных в приложении. """
    # Этот интерфейс подразумевает множественные варианты его реализации.
    # Передаётся (?) между модулями? Или только интерфейсы получателя/отправителя?
    @abstractmethod
    def add_wire(self, new_wire: IWire) -> None:
        """ Добавить канал передачи данных. """
        pass

    @abstractmethod
    def get_wire(self, sender: AppModulesEnum, receiver: AppModulesEnum, data_type: DataTypeEnum) -> IWire:
        """ Получить канал передачи данных. """
        pass

    @abstractmethod
    def get_in_wires(self, receiver: AppModulesEnum) -> Tuple[ISender]:
        """ Получить все входящие интерфейсы данного блока приложения. """
        pass

    @abstractmethod
    def get_out_wires(self, sender: AppModulesEnum) -> Tuple[IReceiver]:
        """ Получить все исходящие интерфейсы данного блока приложения. """
        pass
