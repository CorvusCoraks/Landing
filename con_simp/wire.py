""" Канал передачи данных с помощью носителей-вагонеток. """
from con_intr.ifaces import TransferredData, AppModulesEnum, DataTypeEnum, IContainer, IReceiver, ISender, IWire
from queue import Queue


class Wire(IWire):
    """ Односторонний канал передачи данных. Внутри очередь передачи непосредственно объектов. """
    def __init__(self, sender: AppModulesEnum, receiver: AppModulesEnum, data_type: DataTypeEnum):
        super().__init__(sender, receiver, data_type)

        self.__sender: AppModulesEnum = sender
        self.__receiver: AppModulesEnum = receiver
        self.__type: DataTypeEnum = data_type

        self.__queue: Queue = Queue()

    def send(self, cargo: IContainer) -> None:
        """ Отправить данные, ожидающие отправления. """
        self.__queue.put(cargo)

    def get_receiver(self) -> AppModulesEnum:
        """ Кто получатель? """
        return self.__receiver

    def get_sending_type(self) -> DataTypeEnum:
        """ Какой тип данных передаётся? """
        return self.__type

    def receive(self) -> IContainer:
        """ Получить ожидающие данные. """
        return self.__queue.get()

    def has_incoming(self) -> bool:
        """ Имеются ли входящие данные? """
        return not self.__queue.empty()

    def get_sender(self) -> AppModulesEnum:
        """ Кто отправитель? """
        return self.__sender

    def get_receiving_type(self) -> DataTypeEnum:
        """ Какой тип данных? """
        return self.__type


class ReportWire(Wire):
    def __init__(self, sender: AppModulesEnum, receiver: AppModulesEnum, data_type: DataTypeEnum, report_type: DataTypeEnum):
        super().__init__(sender, receiver, data_type)

        self.__report_wire = Wire(receiver, sender, report_type)

    def get_report_sender(self) -> ISender:
        """ Получить интерфейс отправителя рапортов. """
        return self.__report_wire

    def get_report_receiver(self) -> IReceiver:
        """ Получить интерфейс получателя рапортов. """
        return self.__report_wire
