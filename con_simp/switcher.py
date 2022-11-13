""" Общий объект агрегирующий каналы передачи данных. """
from con_intr.ifaces import ISwitchboard, AppModulesEnum, IReceiver, ISender, DataTypeEnum, ISocket
from con_simp.wire import Wire
from typing import List, Tuple, Optional


class Switchboard(ISwitchboard):
    def __init__(self):
        self.__wires: List[Wire] = list()

    def add_wire(self, new_wire: Wire) -> None:
        self.__wires.append(new_wire)

    def get_wire(self, sender: AppModulesEnum, receiver: AppModulesEnum, data_type: DataTypeEnum) -> Wire:
        for value in self.__wires:
            if value.get_sender() == sender and value.get_receiver() == receiver \
                    and value.get_receiving_type() == data_type:
                return value

    def get_all_in(self, receiver: AppModulesEnum) -> Tuple[ISender]:
        result: List[ISender] = list()
        for value in self.__wires:
            if value.get_receiver() == receiver:
                result.append(value)
        return tuple(result)

    def get_all_out(self, sender: AppModulesEnum) -> Tuple[IReceiver]:
        result: List[IReceiver] = list()
        for value in self.__wires:
            if value.get_sender() == sender:
                result.append(value)
        return tuple(result)


class Socket(ISocket):
    def __init__(self, module: AppModulesEnum, switchboard: ISwitchboard):
        self.__module = module
        self.__switchboard = switchboard

    def get_all_in(self) -> Tuple[ISender]:
        return  self.__switchboard.get_all_in(self.__module)

    def get_all_out(self) -> Tuple[IReceiver]:
        return self.__switchboard.get_all_out(self.__module)