""" Общий объект агрегирующий каналы передачи данных. """
from con_intr.ifaces import ISwitchboard, AppModulesEnum, IReceiver, ISender, DataTypeEnum, ISocket
from con_simp.wire import Wire
from typing import List, Tuple, Optional, Dict


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

    def get_all_in(self, receiver: AppModulesEnum) -> Tuple[IReceiver]:
        result: List[IReceiver] = list()
        for value in self.__wires:
            if value.get_receiver() == receiver:
                result.append(value)
        return tuple(result)

    def get_all_out(self, sender: AppModulesEnum) -> Tuple[ISender]:
        result: List[ISender] = list()
        for value in self.__wires:
            if value.get_sender() == sender:
                result.append(value)
        return tuple(result)


class Socket(ISocket):
    def __init__(self, module: AppModulesEnum, switchboard: ISwitchboard):
        self.__module = module
        self.__switchboard = switchboard

    def get_all_in(self) -> Tuple[IReceiver]:
        return  self.__switchboard.get_all_in(self.__module)

    def get_all_out(self) -> Tuple[ISender]:
        # test = self.__switchboard.get_all_out(self.__module)
        return self.__switchboard.get_all_out(self.__module)

    def get_in_dict(self) -> Dict[AppModulesEnum, Dict[DataTypeEnum, IReceiver]]:
        """ Доступ к интерфейсам получателя через двойной словарь по двум ключам (AppModuleEnum и DataTypeEnum). """

        # итоговое отображение в виде словаря
        incoming: Dict[AppModulesEnum, Dict[DataTypeEnum, IReceiver]] = {}
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

    def get_out_dict(self) -> Dict[AppModulesEnum, Dict[DataTypeEnum, ISender]]:
        """ Доступ к интерфейсам отправителя через двойной словарь по двум ключам (AppModuleEnum и DataTypeEnum). """

        # итоговое отображение в виде словаря
        outgoing: Dict[AppModulesEnum, Dict[DataTypeEnum, ISender]] = {}
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