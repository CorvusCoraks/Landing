""" Интерфейсы инициализируемых состояний и хранилища текущих состояний. """
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, overload
from app_type import TestId
from structures import RealWorldStageStatusN

# IIninitStates -> InitGanerator
#           └> another interaface realization
# IStatesStore -> DictStore
#           └> another interface realization


class IInitStates(ABC):
    """ Интерфейс инициализации начальных состояний новых испытаний. """
    @abstractmethod
    def __init__(self, max_tests: Optional[int]):
        """

        :param max_tests: Максимальное запланированное количество испытаний.
        """
        ...

    @abstractmethod
    def get_state(self) -> Optional[Tuple[Optional[TestId], RealWorldStageStatusN]]:
        """ Получить новое начальное состояние нового испытания.

        :return: Если == None, то запас начальных состояний иссяк.
        """
        # Если  TestId == None, то это должно быть явно отражено в выходе метода:
        # return None, state
        ...

    @abstractmethod
    def get_amount(self) -> int:
        """ Получить оставшееся количество начальных состояний новых испытаний.

        :return:
        """
        ...


class IStatesStore(ABC):
    """ Интерфейс хранилища состояний, которые уже находятся в работе (т. е. завершившихся здесь нет). """
    @abstractmethod
    def get_state(self, test_id: TestId) -> Optional[RealWorldStageStatusN]:
        """ Получить текущее состояние испытания.

        :param test_id: Идентификатор испытания.
        :return: Если == None, значит состояние с таким test_id отсутствует, и вернуть его из метода не получилось.
        """
        ...

    @abstractmethod
    def update_state(self, test_id: TestId, state: RealWorldStageStatusN) -> bool:
        """ Обновить состояние.

        :param test_id:
        :param state:
        :return: Если == False, значит испытание с таким test_id не существует, и обновить не получилось.
        """
        ...

    @overload
    @abstractmethod
    def add_state(self, states: Dict[TestId, RealWorldStageStatusN]) -> bool:
        ...

    @overload
    @abstractmethod
    def add_state(self, test_id: TestId, state: RealWorldStageStatusN) -> bool:
        ...

    @abstractmethod
    def add_state(self, states: Optional[Dict[TestId, RealWorldStageStatusN]] = None,
                  test_id: Optional[TestId] = None, state: Optional[RealWorldStageStatusN] = None) -> bool:
        """ Добавить в хранилище состояний новое состояние (целый словарь или одно)

        :param states: Словарь состояний (overload 1)
        :param test_id: Идентификатор состояния (overload 2)
        :param state: Состояние (overload 2)
        :return: Если == False, значит добавляемые состояния уже есть в хранилище - ошибка!
        """
        ...

    @abstractmethod
    def del_state(self, test_id: TestId) -> bool:
        """ Удалить испытание.

        :param test_id:
        :return: Если == False, значит испытания с таким test_id не существует, и удалить его не получилось.
        """
        ...

    @abstractmethod
    def get_amount(self) -> int:
        """ Получить текущее количество состояний в работе. """
        ...

    @abstractmethod
    def all_states(self) -> Dict[TestId, RealWorldStageStatusN]:
        """ Получить словарь всех текущих испытаний. """
        ...
