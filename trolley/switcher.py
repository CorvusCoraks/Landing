""" Общий объект агрегирующий каналы передачи данных. """
from con_intr.ifaces import ISwitchboard, AppModulesEnum, IReceiver, ISender, DataTypeEnum, IWire


class TrolleySwitchBoard(ISwitchboard):
    def add_wire(self, new_wire: IWire) -> None:
        pass

    def get_wire(self, sender: AppModulesEnum, receiver: AppModulesEnum, data_type: DataTypeEnum) -> IWire:
        pass

    def get_in_wires(self, receiver: AppModulesEnum) -> ISender:
        pass

    def get_out_wires(self, sender: AppModulesEnum) -> IReceiver:
        pass
