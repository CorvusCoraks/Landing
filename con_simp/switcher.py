""" Общий объект агрегирующий каналы передачи данных. """
from con_intr.ifaces import ISwitchboard, IReceiver, ISender, ISocket, A, D, IWire, IFinishApp, DataTypeEnum
from con_simp.wire import Wire
from con_simp.contain import Container
from typing import List, Tuple, Dict, Optional, Type
from basics import FinishAppException


class Switchboard(ISwitchboard):
    def __init__(self):
        # Список с каналами передачи данных.
        self.__wires: List[Wire] = list()

    def _is_unique(self, new_wire: IWire) -> bool:
        if self.get_wire(new_wire.get_sender(), new_wire.get_receiver(), new_wire.get_sending_type()) is None:
            return True
        else:
            return False

    def add_wire(self, new_wire: Wire) -> None:
        assert self._is_unique(new_wire) is True, "Adding wire have a equal parameters (Sender, Receiver, Data Type) " \
                                                  "with wire added earlier. Adding wire should be a unique object."
        self.__wires.append(new_wire)

    def get_wire(self, sender: A, receiver: A, data_type: D) -> Optional[Wire]:
        for value in self.__wires:
            if value.get_sender() == sender and value.get_receiver() == receiver \
                    and value.get_receiving_type() == data_type:
                return value

        return None

    def get_all_in(self, receiver: A) -> Tuple[IReceiver]:
        result: List[IReceiver] = list()
        for value in self.__wires:
            if value.get_receiver() == receiver:
                result.append(value)
        return tuple(result)

    def get_all_out(self, sender: A) -> Tuple[ISender]:
        result: List[ISender] = list()
        for value in self.__wires:
            if value.get_sender() == sender:
                result.append(value)
        return tuple(result)


class Socket(ISocket):
    def __init__(self, module: A, switchboard: ISwitchboard):
        """

        :param module: Модуль приложения, для которого создаётся Сокет.
        :param switchboard: Объект, содержащий ВСЕ каналы связи приложения.
        """
        self.__module = module
        self.__switchboard = switchboard

    def get_all_in(self) -> Tuple[IReceiver]:
        return self.__switchboard.get_all_in(self.__module)

    def get_all_out(self) -> Tuple[ISender]:
        return self.__switchboard.get_all_out(self.__module)

    def get_in_dict(self) -> Dict[A, Dict[D, IReceiver]]:
        # итоговое отображение в виде словаря
        incoming: Dict[A, Dict[D, IReceiver]] = {}
        # перебор всех входящих каналов передачи данных
        for ireceiver in self.get_all_in():
            # первый ключ в итоговом словаре
            key = ireceiver.get_sender()
            # Если в итоговом словаре нет очередного ключа (отправителя данных), то создаём пустой "словарь-в-словаре"
            if key not in incoming:
                incoming[key] = {}
            # Так как теперь в любом случае в итоговом словаре ключ (отправитель данных) и "словарь-в-словаре" есть,
            # то записываем новый элемент в "словарь-в-словаре" по этому ключу.
            incoming[key][ireceiver.get_receiving_type()] = ireceiver
        return incoming

    def get_out_dict(self) -> Dict[A, Dict[D, ISender]]:
        # итоговое отображение в виде словаря
        outgoing: Dict[A, Dict[D, ISender]] = {}
        # перебор всех исходящих каналов передачи данных
        for isender in self.get_all_out():
            # первый ключ в итоговом словаре
            key = isender.get_receiver()
            # Если в итоговом словаре нет очередного ключа (получателя данных), то создаём пустой "словарь-в-словаре"
            if key not in outgoing:
                outgoing[key] = {}
            # Так как теперь в любом случае в итоговом словаре ключ (получатель данных) и "словарь-в-словаре" есть,
            # то записываем новый элемент в "словарь-в-словаре" по этому ключу.
            outgoing[key][isender.get_sending_type()] = isender
        return outgoing


class AppFinish(IFinishApp):
    """ Класс взаимодействия с каналами передачи команд на завершение приложения. """
    def __init__(self, socket: ISocket):
        """

        :param socket: интерфейс взаимодействия данного абонента со средой передачи сообщений.
        """
        # Список ИСХОДЯЩИХ каналов, предназначенных для передачи команды на завершение приложения.
        self.__outgoing_wires: list[ISender] = []
        # Список ВХОДЯЩИХ каналов, предназначенных для передачи команды на завершение приложения.
        self.__incoming_wires: list[IReceiver] = []

        for sender in socket.get_all_out():
            # Перебираем все исходящие каналы
            if sender.get_sending_type() == DataTypeEnum.APP_FINISH:
                # И отбираем только те, которые предназначены для передачи сообщения о завершении приложения.
                self.__outgoing_wires.append(sender)

        for receiver in socket.get_all_in():
            # Перебираем все входящие каналы
            if receiver.get_receiving_type() == DataTypeEnum.APP_FINISH:
                # И отбираем только те, которые предназначены для передачи сообщения о завершении приложения.
                self.__incoming_wires.append(receiver)

    def send_stop_app(self) -> None:
        for sender in self.__outgoing_wires:
            sender.send(Container())

    def finish_app_checking(self) -> None:
        for receiver in self.__incoming_wires:
            if receiver.has_incoming():
                receiver.receive()
                raise FinishAppException
