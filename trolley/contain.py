""" Разнообразные контейнеры. """
from con_intr.ifaces import TransferredData, About, IContainer
from typing import Optional

TestId = int


class Container(IContainer):
    """ Простой контейнер с идентификатором теста. """
    def __init__(self):
        self.__cargo: Optional[TransferredData] = None
        self.__test_id: TestId = -1

    def pack(self, cargo: TransferredData) -> None:
        self.__cargo = cargo

    def unpack(self) -> TransferredData:
        return self.__cargo

    def set(self, about: About) -> None:
        self.__test_id = about

    def get(self) -> About:
        return self.__test_id