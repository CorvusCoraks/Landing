""" Канал передачи данных с помощью носителей-вагонеток. """
from con_intr.ifaces import IContainer, IReceiver, ISender, IWire, A, D
from queue import Queue


class Wire(IWire):
    """ Односторонний канал передачи данных. Внутри очередь передачи непосредственно объектов. """
    def __init__(self, sender: A, receiver: A, data_type: D):
        """

        :param sender: Отправитель данных.
        :param receiver: Получатель данных.
        :param data_type: Тип передаваемых данных.
        """
        super().__init__(sender, receiver, data_type)

        self.__sender: A = sender
        self.__receiver: A = receiver
        self.__type: D = data_type

        # Очередь передачи данных.
        self.__queue: Queue = Queue()

    def send(self, cargo: IContainer) -> None:
        self.__queue.put(cargo)

    def get_receiver(self) -> A:
        return self.__receiver

    def get_sending_type(self) -> D:
        return self.__type

    def receive(self) -> IContainer:
        return self.__queue.get()

    def has_incoming(self) -> bool:
        return not self.__queue.empty()

    def get_sender(self) -> A:
        return self.__sender

    def get_receiving_type(self) -> D:
        return self.__type


class ReportWire(Wire):
    """ Двусторонний канал передачи данных. """
    def __init__(self, sender: A, receiver: A, data_type: D, report_type: D):
        """

        :param sender: Отправитель данных.
        :param receiver: Получатель данных.
        :param data_type: Тип передаваемых в прямом направлении данных.
        :param report_type: Тип передаваемых в обратном направлении данных.
        """
        super().__init__(sender, receiver, data_type)

        # Линия рапорта, для передачи данных в обратном направлении.
        self.__report_wire = Wire(receiver, sender, report_type)

    def get_report_sender(self) -> ISender:
        """ Получить интерфейс отправителя рапортов. """
        return self.__report_wire

    def get_report_receiver(self) -> IReceiver:
        """ Получить интерфейс получателя рапортов. """
        return self.__report_wire
