""" ISwitchboard - интерфейс объекта очередей сообщений приложения. """
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Tuple, Optional, overload


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

    # # todo Нужен ли этот метод?
    # @abstractmethod
    # def has_outgoing(self) -> bool:
    #     """ Имеются ли данные для отправления? """
    #     pass

    # # todo Нужен ли этот метод в интерфейсе отправителя, ведь отправитель устанавливается при создании канала
    # @abstractmethod
    # def set_receiver(self, receiver: AppModulesEnum) -> None:
    #     """ Установить получателя данных. """
    #     pass

    @abstractmethod
    def get_receiver(self) -> AppModulesEnum:
        """ Кто получатель? """
        pass

    # # todo Нужен ли этот метод в интерфейсе отправителя, ведь тип данных устанавливается при создании канала
    # @abstractmethod
    # def set_sending_type(self, data_type: DataTypeEnum) -> None:
    #     """ Установить тип отправляемых данных. """
    #     pass

    @abstractmethod
    def get_sending_type(self) -> DataTypeEnum:
        """ Какой тип данных передаётся? """
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
    @abstractmethod
    def __init__(self, sender: AppModulesEnum, receiver: AppModulesEnum, data_type: DataTypeEnum):
        pass

    @abstractmethod
    def send(self, container: IContainer) -> None:
        """ Отправить данные, ожидающие отправления. """
        pass

    # @abstractmethod
    # def has_outgoing(self) -> bool:
    #     """ Имеются ли данные для отправления? """
    #     pass

    @abstractmethod
    def get_receiver(self) -> AppModulesEnum:
        """ Кто получатель? """
        pass

    @abstractmethod
    def get_sending_type(self) -> DataTypeEnum:
        """ Какой тип данных передаётся? """
        pass

    # @abstractmethod
    # def set_receiver(self, receiver: AppModulesEnum) -> None:
    #     """ Установить получателя данных. """
    #     pass
    #
    # @abstractmethod
    # def set_sending_type(self, data_type: DataTypeEnum) -> None:
    #     """ Установить тип отправляемых данных. """
    #     pass

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


# class ISocket(ABC):
#     """ Специальный интерфейс для передачи его в вычислительные модули приложения. """
#     @overload
#     def get_in_wires(self, receiver: None) -> Optional[Tuple[ISender]]:
#         """ Получить все входящие интерфейсы данного блока приложения. Метод для передачи внутрь конкретного модуля. """
#         ...
#
#     @abstractmethod
#     def get_in_wires(self, receiver: Optional[AppModulesEnum]) -> Optional[Tuple[ISender]]:
#         """ Получить все входящие интерфейсы данного блока приложения. """
#         pass
#
#     @overload
#     def get_out_wires(self, sender: None) -> Optional[Tuple[IReceiver]]:
#         """ Получить все исходящие интерфейсы данного блока приложения. Метод для передачи внутрь конкретного модуля."""
#         ...
#
#     @abstractmethod
#     def get_out_wires(self, sender: Optional[AppModulesEnum]) -> Optional[Tuple[IReceiver]]:
#         """ Получить все исходящие интерфейсы данного блока приложения. """
#         pass


class ISocket(ABC):
    """ Специальный интерфейс для передачи его в вычислительные модули приложения. """
    @abstractmethod
    def get_all_in(self) -> Tuple[ISender]:
        """ Получить все входящие интерфейсы данного блока приложения."""
        pass


    @abstractmethod
    def get_all_out(self) -> Tuple[IReceiver]:
        """ Получить все исходящие интерфейсы данного блока приложения."""
        pass



# class IModuleSocket(ABC):
#     @abstractmethod
#     def get_in_wires(self) -> Tuple[ISender]:
#         """ Получить все входящие интерфейсы данного блока приложения. """
#         pass
#
#     # @overload
#     # def get_out_wires(self, sender: None) -> Tuple[IReceiver]:
#     #     """ Получить все исходящие интерфейсы данного блока приложения. """
#     #     ...
#
#     @abstractmethod
#     def get_out_wires(self) -> Tuple[IReceiver]:
#         """ Получить все исходящие интерфейсы данного блока приложения. """
#         pass

class ISwitchboard(ABC):
    """ Интерфейс класса объединяющего все каналы передачи данных в приложении. """
    # Этот интерфейс подразумевает множественные варианты его реализации.
    #
    # Отправитель, получатель, тип передаваемых данных - однозначно идентифицируют канал.
    # Двух каналов с данными одинаковыми параметрами существовать не может.
    #
    # В реализации методов get_in_wires() get_out_wires() обеспечить варианты обработки перегруженных методов
    # интерфейса ISocket (входной параметр Null - возвращает Null)
    @abstractmethod
    def add_wire(self, new_wire: IWire) -> None:
        """ Добавить канал передачи данных. """
        pass

    @abstractmethod
    def get_wire(self, sender: AppModulesEnum, receiver: AppModulesEnum, data_type: DataTypeEnum) -> IWire:
        """ Получить канал передачи данных. """
        pass

    # def get_in_wires(self) -> None:
    #     return None

    @abstractmethod
    def get_all_in(self, receiver: Optional[AppModulesEnum]) -> Optional[Tuple[ISender]]:
        """ Получить все входящие интерфейсы данного блока приложения. """
        pass

    @abstractmethod
    def get_all_out(self, sender: Optional[AppModulesEnum]) -> Optional[Tuple[IReceiver]]:
        """ Получить все исходящие интерфейсы данного блока приложения. """
        pass



# class Socket(ISocket):
#     def __init__(self, module: AppModulesEnum, switchboard: ISwitchboard):
#         self.__module = module
#         self.__switchboard = switchboard
#
#     def get_all_in_wires(self, receiver: None) -> Tuple[ISender]:
#         return  self.__switchboard.get_in_wires(self.__module)
#
#     def get_out_wires(self, sender: None) -> Tuple[IReceiver]:
#         return self.__switchboard.get_out_wires(self.__module)