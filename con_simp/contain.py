""" Разнообразные контейнеры. """
from con_intr.ifaces import TransferredData, About, IContainer, BioEnum
from typing import Optional, Tuple
from basics import TestId


class Container(IContainer):
    """ Простой контейнер с идентификатором теста. """
    def __init__(self, test_id=-1, cargo=None ):
        """

        :param test_id: Идентификатор испытания.
        :param cargo: Пакуемый в контейнер груз.
        """
        self.__cargo: Optional[TransferredData] = cargo
        self.__test_id: TestId = test_id

    def pack(self, cargo: TransferredData) -> None:
        self.__cargo = cargo

    def unpack(self) -> TransferredData:
        return self.__cargo

    def set(self, test_id: TestId) -> None:
        self.__test_id = test_id

    def get(self) -> TestId:
        return self.__test_id


class BioContainer(IContainer):
    """ Контейнер содержащий дополнительно идентификатор теста и Bio-статус """
    def __init__(self, test_id=-1, bio=BioEnum.ALIVE, cargo=None):
        """

        :param test_id: Идентификатор испытания
        :param bio: Состояние данного испытания.
        :param cargo: Данные, содержащиеся в контейнере.
        """
        self.__cargo: Optional[TransferredData] = cargo
        self.__test_id: TestId = test_id
        self.__bio: BioEnum = bio
    def pack(self, cargo: TransferredData) -> None:
        self.__cargo = cargo

    def unpack(self) -> TransferredData:
        return self.__cargo

    def set(self, about: Tuple[TestId, BioEnum]) -> None:
        self.__test_id, self.__bio = about[0], about[1]

    def get(self) -> Tuple[TestId, BioEnum]:
        return self.__test_id, self.__bio