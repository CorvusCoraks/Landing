from typing import Optional, Tuple, Dict, List, overload

from states.i_states import IStatesStore, IInitStates
from basics import TestId
from structures import RealWorldStageStatusN
# from typing import Dict
from copy import deepcopy


class DictStore(IStatesStore):
    """ Хранилище состояний испытаний в виде словаря. """
    def __init__(self):
        self.__ongoing_states: Dict[TestId, RealWorldStageStatusN] = {}

    def get_state(self, test_id: TestId) -> Optional[RealWorldStageStatusN]:
        try:
            return self.__ongoing_states[test_id]
        except KeyError:
            return None

    def update_state(self, test_id: TestId, state: RealWorldStageStatusN) -> bool:
        try:
            # Если ключа нет, будет инициировано исключение
            temp = self.__ongoing_states[test_id]
        except KeyError:
            return False
        else:
            # Если ключ есть, успешно обновляем.
            self.__ongoing_states[test_id] = state
            return True

    def add_state(self, states: Dict[TestId, RealWorldStageStatusN] = None, test_id: TestId = None, state: RealWorldStageStatusN = None):
        # Реализация @overload методов родительского интерфейса.
        if states is not None and test_id is None and state is None:
            # Добавление набора состояний в виде словаря. Если уже есть испытания с такими идентификаторами,
            # то их состояния перезаписываются.
            self.__ongoing_states.update(states)
        elif states is None and test_id is not None and state is not None:
            # Добавление состояния по его ключу. Если уже есть такое состояние, то оно перезапишется.
            self.__ongoing_states[test_id] = state
        else:
            raise TypeError("Bad arguments of overload method.")

    def del_state(self, test_id: TestId) -> bool:
        try:
            # Если ключа нет, то всё плохо
            temp = self.__ongoing_states[test_id]
        except KeyError:
            return False
        else:
            # Если ключ уже есть, то всё хорошо
            self.__ongoing_states.pop(test_id)
            return True

    def get_amount(self) -> int:
        return len(self.__ongoing_states)

    def all_states(self) -> Dict[TestId, RealWorldStageStatusN]:
        return deepcopy(self.__ongoing_states)


class InitGenerator(IInitStates):
    def get_state(self) -> Optional[Tuple[Optional[TestId], RealWorldStageStatusN]]:
        pass

    def get_amount(self) -> int:
        pass