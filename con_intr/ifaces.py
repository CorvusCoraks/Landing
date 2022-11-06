""" ISwitchboard - интерфейс объекта очередей сообщений приложения. """
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


# Тип данных (уровня семантики Python), передаваемых между функциональными блоками приложения.
TransferredData = Any
# Дополнительная информация о блоке данных
About = Any


class AppModulesEnum(Enum):
    """ Константы, определяющие функциональные блоки приложения. """
    MAIN = 0
    VIEW = 1
    PHYSICS = 2
    NEURO = 3


class DataTypeEnum(Enum):
    """ Константы, определяющие тип (тип, в смысле функционала приложения) передаваемых данных. """
    REMANING_TESTS = 0
    STAGE_STATUS = 1


#
# Интерфейсы передаваемых данных
#


class IExtra(ABC):
    """ Идентификатор (любая дополнительная информ.) груза, определяющий, например, место груза в потоке испытаний. """
    @abstractmethod
    def set(self, about: About) -> None:
        pass

    @abstractmethod
    def get(self) -> About:
        pass


class ICargo(ABC):
    """ Универсальный контейнер, который содержит некий груз. """
    @abstractmethod
    def pack(self, cargo: TransferredData) -> None:
        pass

    @abstractmethod
    def unpack(self) -> TransferredData:
        pass


class IContainer(ICargo, IExtra):
    """ Универсальный контейнер, который содержит некий груз и дополнительные данные к нему. """
    @abstractmethod
    def pack(self, cargo: TransferredData) -> None:
        pass

    @abstractmethod
    def unpack(self) -> TransferredData:
        pass

    @abstractmethod
    def set(self, about: About) -> None:
        pass

    @abstractmethod
    def get(self) -> About:
        pass


#
# Интерфейсы получателя и отправителя
#


class ISender(ABC):
    """ Интерфейс отправителя данных. """
    @abstractmethod
    def send(self, container: IContainer) -> None:
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
    def receive(self) -> IContainer:
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


#
# Интерфейсы индивидуального канала и распределительного щита
#


class IWire(ISender, IReceiver):
    """ Интерфейс канала передачи данных. """
    # Подразумевает множественные варианты конкретной реализации.
    # def __init__(self, sender: AppModulesEnum, reseiver: AppModulesEnum, data_type: DataTypeEnum):
    #     pass

    @abstractmethod
    def send(self, container: IContainer) -> None:
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

    @abstractmethod
    def receive(self) -> IContainer:
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
    def get_in_wires(self, receiver: AppModulesEnum) -> ISender:
        """ Получить все входящие интерфейсы данного блока приложения. """
        pass

    @abstractmethod
    def get_out_wires(self, sender: AppModulesEnum) -> IReceiver:
        """ Получить все исходящие интерфейсы данного блока приложения. """
        pass
