""" Реализация хранилища испытаний в виде словаря. """
from typing import Optional, Tuple, Dict, List, overload
from states.i_states import IStatesStore, IInitStates
from app_type import TestId
from structures import RealWorldStageStatusN
# from typing import Dict
from copy import deepcopy
from states.iterable import InitialStatusAbstract, InitialStatus


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

    def add_state(self, states: Dict[TestId, RealWorldStageStatusN] = None, test_id: TestId = None, state: RealWorldStageStatusN = None) -> bool:
        # Реализация @overload методов родительского интерфейса.
        if states is not None and test_id is None and state is None:
            # Добавление набора состояний в виде словаря.
            # Находим пересечение множества ключей хранящихся состояний и множества ключей добавляемых состояний.
            # Если пересечение не нулевое, значит в хранилище уже есть данные
            # по какому-то добавляемому испытанию - ошибка.
            set_ongoing = set(self.__ongoing_states.keys()).intersection(set(states.keys()))
            if len(set_ongoing) != 0:
                # В хранилище есть данные по какому-то добавляемому испытанию - ошибка.
                # Возможна несанкционированная перезапись.
                assert len(set_ongoing) == 0, "Keys is already in storage: {}".format(set_ongoing)
                return False
            else:
                self.__ongoing_states.update(states)
                # self.__ongoing_states |= states
                return True
        elif states is None and test_id is not None and state is not None:
            # Добавление состояния по его ключу.
            if test_id in set(self.__ongoing_states.keys()):
                # Ключ уже присутствует в хранилище - ошибка.
                # Возможна несанкционированная перезапись.
                assert test_id in set(self.__ongoing_states.keys()), "Key is already in storage: {}".format(test_id)
                return False
            else:
                self.__ongoing_states[test_id] = state
                return True
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

    def __init__(self, max_tests: int):
        self.__max_tests: int = max_tests
        self._initial = InitialStatus(self.__max_tests)
        self.__iter = iter(self._initial)

    def get_state(self) -> Optional[Tuple[Optional[TestId], RealWorldStageStatusN]]:
        return next(self.__iter)

    def get_amount(self) -> int:
        return self._initial.remaining_count()