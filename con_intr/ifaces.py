""" ISwitchboard - интерфейс объекта очередей сообщений приложения. """
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Tuple, Optional, overload, Dict, TypeVar, Type


# Тип данных (уровня семантики Python), передаваемых между функциональными блоками приложения.
TransferredData = Any
# Дополнительная информация о блоке данных
About = Any

# Sender and Receiver _Abonent_ Type Enum
A = TypeVar('A', bound=Enum)
# _Data_ Type Enum
D = TypeVar('D', bound=Enum)

# Словарь входных каналов блока приложения
# AppModulesEnum - отправитель, DataTypeEnum - тип передаваемых данных,
# IReceiver - интерфейс получателя, для получения этих данных
Inbound = Dict['AppModulesEnum', Dict['DataTypeEnum', 'IReceiver']]
# Словарь выходных каналов блока приложения.
# AppModuleEnum - получатель, DataTypeEnum - тип передаваемых данных,
# ISender - интерфейс отправителя, для отправления этих данных.
Outbound = Dict['AppModulesEnum', Dict['DataTypeEnum', 'ISender']]


class AppModulesEnum(Enum):
    """ Константы, определяющие функциональные блоки приложения. """
    MAIN = 0   # главный модуль
    VIEW = 1   # поток отображения
    PHYSICS = 2   # поток физической модели
    NEURO = 3   # поток нейросети


class DataTypeEnum(Enum):
    """ Константы, определяющие тип (тип, в смысле функционала приложения) передаваемых данных. """
    # Количество оставшихся испытаний (и текущих, и в плане)
    REMANING_TESTS = 0  # int
    # Состояние ступени
    STAGE_STATUS = 1    # RealWorldStageStatusN
    # Команда на двигатели
    JETS_COMMAND = 2    # ?
    # Приказ завершить приложение
    APP_FINISH = 3  # True
    # Модуль запрашивает указанное количество тестов
    REQUESTED_TESTS = 4     # int
    # Подкрепление
    REINFORCEMENT = 5
    # Готов перейти к следующему батчу
    # READY_FOR_NEXT_BATCH = 6 # True
    ENV_ROAD = 6 # RoadEnum
    # Запрос на завершение приложения.
    APP_FINISH_REQUEST = 7


class RoadEnum(Enum):
    """ Константы-семафоры для передачи из БНС в БФМ. """
    # Начать новую эпоху
    START_NEW_AGE = 0
    # Остановить обучение.
    ALL_AGES_FINISHED = 1
    # Продолжить работу как есть.
    CONTINUE = 3


class BioEnum(Enum):
    """ Статус состояния изделия. """
    INIT = -1   # Состояние инициализировано.
    ALIVE = 0   # Испытание в работе.
    FIN = 1     # Испытание завершено. Последнее состояние.


#
# Интерфейсы передаваемых данных
#


class IExtra(ABC):
    """ Идентификатор (любая дополнительная информ.) груза, определяющий, например, место груза в потоке испытаний. """
    @abstractmethod
    def set(self, about: About) -> None:
        """ Добавить дополнительные данные.

        :param about: Некоторые дополнительные данные.
        """
        pass

    @abstractmethod
    def get(self) -> About:
        """ Получить дополнительные параметры.

        :return: Дополнительные параметры.
        """
        pass


class ICargo(ABC):
    """ Универсальный контейнер, который содержит некий груз. """
    @abstractmethod
    def pack(self, cargo: D) -> None:
        """ Упаковать данные в контейнер.

        :param cargo: Данные для упаковки.
        """
        pass

    @abstractmethod
    def unpack(self) -> D:
        """ Распаковать данные из контейнера.

        :return: Данные из контейнера.
        """
        pass


class IContainer(ICargo, IExtra):
    """ Универсальный контейнер, который содержит некий груз и дополнительные данные к нему. """
    @abstractmethod
    def pack(self, cargo: D) -> None:
        pass

    @abstractmethod
    def unpack(self) -> D:
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
        """ Отправить данные, ожидающие отправления.

        :param container: Контейнер с данными.
        """
        pass

    @abstractmethod
    def get_receiver(self) -> A:
        """ Кто получатель?

        :return: Получатель контейнера.
        """
        pass

    @abstractmethod
    def get_sending_type(self) -> D:
        """ Какой тип данных передаётся?

        :return: Тип данных, которые содержит контейнер.
        """
        pass


class IReceiver(ABC):
    """ Интерфейс получателя данных """
    @abstractmethod
    def receive(self) -> IContainer:
        """ Получить ожидаемые данные.

        :return: Контейнер с данными.
        """
        pass

    @abstractmethod
    def has_incoming(self) -> bool:
        """ Имеются ли входящие данные?

        :return: True - имеются (и ожидают разгрузки и распаковки), False - данных для получения в канале нет.
        """
        pass

    @abstractmethod
    def get_sender(self) -> A:
        """ Кто отправитель?

        :return: Отправитель данных.
        """
        pass

    @abstractmethod
    def get_receiving_type(self) -> D:
        """ Какой тип данных?

        :return: Тип данных (класс ``DataTypeEnum``), передаваемый по данному каналу
        """
        pass


#
# Интерфейсы индивидуального канала и распределительного щита
#


class IWire(ISender, IReceiver):
    """ Интерфейс канала передачи данных. """
    # Подразумевает множественные варианты конкретной реализации.
    @abstractmethod
    def __init__(self, sender: A, receiver: A, data_type: D):
        """

        :param sender: Отправитель данных данного канала.
        :param receiver: Получатель данных из данного канала.
        :param data_type: Тип данных, передаваемых по данному каналу.
        """
        pass

    @abstractmethod
    def send(self, container: IContainer) -> None:
        pass

    @abstractmethod
    def get_receiver(self) -> A:
        pass

    @abstractmethod
    def get_sending_type(self) -> D:
        pass

    @abstractmethod
    def receive(self) -> IContainer:
        pass

    @abstractmethod
    def has_incoming(self) -> bool:
        pass

    @abstractmethod
    def get_sender(self) -> A:
        pass

    @abstractmethod
    def get_receiving_type(self) -> D:
        pass


class ISocket(ABC):
    """ Специальный интерфейс (в общем смысле) взаимодействия абонента со средой передачи сообщений. """
    # Т. е., собственно, с экземпляром класса реализующего ISwitchboard
    # todo Сделать защищённым или приватным?
    @abstractmethod
    def get_all_in(self) -> Tuple[IReceiver]:
        """ Получить все входящие интерфейсы данного блока приложения.

        :return: Кортеж с интерфейсами предназначенными для работы получателя данных.
        """
        pass

    # todo Сдеалать защищённым или приватным?
    @abstractmethod
    def get_all_out(self) -> Tuple[ISender]:
        """ Получить все исходящие интерфейсы данного блока приложения.

        :return: Кортеж с интерфейсами, предназначенными для работы отправителя данных.
        """
        pass

    @abstractmethod
    def get_in_dict(self) -> Dict[A, Dict[D, IReceiver]]:
        """ Доступ к интерфейсам получателя через двойной словарь по двум ключам (Отправитель и Тип данных).

        :return: Словарь словарей. Первый ключ - Отправитель, второй ключ - тип данных,
        значение - интерфейс для получения данных от этого Отправителя.
        """
        ...

    @abstractmethod
    def get_out_dict(self) -> Dict[A, Dict[D, ISender]]:
        """ Доступ к интерфейсам отправителя через двойной словарь по двум ключам (Получатель и Тип данных).

        :return: Словарь словарей. Первый ключ - получатель передаваемых данных, второй ключ - Тип данных,
        значение - интерфейс для передачи данных этому Получателю.
        """
        ...


class ISwitchboard(ABC):
    """ Интерфейс класса объединяющего все каналы передачи данных в приложении. """
    #
    # Этот интерфейс подразумевает множественные варианты его реализации.
    #
    # Отправитель, получатель, тип передаваемых данных - однозначно идентифицируют канал.
    # Двух каналов с данными одинаковыми параметрами существовать не может.
    #
    @abstractmethod
    def _is_unique(self, new_wire: IWire) -> bool:
        """ Метод проверки добавляемого объекта на уникальность. Вызывается внутри метода *add_wire()*

        :param new_wire: Новый канал передачи данных.
        :return: True - канал уникален, False - канал не уникален.
        """
        pass

    @abstractmethod
    def add_wire(self, new_wire: IWire) -> None:
        """ Добавить канал передачи данных.

        :param new_wire: Новый канал передачи данных.
        """
        pass

    @abstractmethod
    def get_wire(self, sender: A, receiver: A, data_type: D) -> Optional[IWire]:
        """ Получить канал передачи данных.

        :param sender: Отправитель данных.
        :param receiver: Получатель данных.
        :param data_type: Тип передаваемых данных.
        :return: Канал передачи данных. Если None, значит канал с этими параметрами не найден.
        """
        pass

    @abstractmethod
    def get_all_in(self, receiver: A) -> Tuple[IReceiver]:
        """ Получить все входящие интерфейсы данного блока приложения.

        :param receiver: Получатель данных.
        :return: Кортеж ВСЕХ входящих линий данного получателя.
        """
        pass

    @abstractmethod
    def get_all_out(self, sender: A) -> Tuple[ISender]:
        """ Получить все исходящие интерфейсы данного блока приложения.

        :param sender: Отправитель данных.
        :return: Кортеж ВСЕХ  исходящий линий данного отправителя.
        """
        pass
