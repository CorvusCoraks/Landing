""" Канал передачи данных с помощью носителей-вагонеток. """
from con_intr.ifaces import TransferredData, AppModulesEnum, DataTypeEnum, IReceiver, ISender, IWire


class TrolleyWires(IWire):
    """ Односторонний канал передачи данных. """
    def send(self, cargo: TransferredData) -> None:
        """ Отправить данные, ожидающие отправления. """
        pass

    def has_outgoing(self) -> bool:
        """ Имеются ли данные для отправления? """
        pass

    def set_receiver(self, receiver: AppModulesEnum) -> None:
        """ Установить получателя данных. """
        pass

    def set_sending_type(self, data_type: DataTypeEnum) -> None:
        """ Установить тип отправляемых данных. """
        pass

    def receive(self) -> TransferredData:
        """ Получить ожидающие данные. """
        pass

    def has_incoming(self) -> bool:
        """ Имеются ли входящие данные? """
        pass

    def get_sender(self) -> AppModulesEnum:
        """ Кто отправитель? """
        pass

    def get_receiving_type(self) -> DataTypeEnum:
        """ Какой тип данных? """
        pass


class ReportedTrolleyWires(IWire):
    """ Канал передачи данных с обратным каналом рапорта. """
    def __init__(self, report_wire: IWire):
        self.__report_wire: IWire = report_wire

    def get_report_sending_interface(self) -> ISender:
        """ Получить интерфейс отправителя рапортов. """
        return self.__report_wire

    def get_report_receiving_interface(self) -> IReceiver:
        """ Получить интерфейс получателя рапортов. """
        return self.__report_wire

    def send(self, cargo: TransferredData) -> None:
        """ Отправить данные, ожидающие отправления. """
        pass

    def has_outgoing(self) -> bool:
        """ Имеются ли данные для отправления? """
        pass

    def set_receiver(self, receiver: AppModulesEnum) -> None:
        """ Установить получателя данных. """
        pass

    def set_sending_type(self, data_type: DataTypeEnum) -> None:
        """ Установить тип отправляемых данных. """
        pass

    def receive(self) -> TransferredData:
        """ Получить ожидающие данные. """
        pass

    def has_incoming(self) -> bool:
        """ Имеются ли входящие данные? """
        pass

    def get_sender(self) -> AppModulesEnum:
        """ Кто отправитель? """
        pass

    def get_receiving_type(self) -> DataTypeEnum:
        """ Какой тип данных? """
        pass