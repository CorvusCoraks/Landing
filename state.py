""" Реализация состояния. """
from typing import Dict, Optional
from nn_iface.if_state import DictKey, InterfaceStorage, ProcessStateInterface


class State(ProcessStateInterface):
    """ Класс состояния процесса обучения. """
    def __init__(self):
        # Словарь с данными.
        # Приложение хранит данные (и изменяет их) во время исполнения в этом словаре.
        self.__proxy_dict: Dict = {DictKey.BATCH_SIZE: -1,
                                   DictKey.EPOCH: [0, 0, 0],
                                   DictKey.ACTOR_OPTIMIZER_STATE: None,
                                   DictKey.CRITIC_OPTIMIZER_STATE: None,
                                   DictKey.TEMP_FOR_TEST: 0}

    def save(self, storage: InterfaceStorage) -> None:
        self.__proxy_dict[DictKey.TEMP_FOR_TEST] += 1

        #словарь с ключами типа строка
        state_dict: dict = {}

        # Преобразование словаря с ключами DictKey в словарь с ключами-строками.
        for key, value in self.__proxy_dict.items():
            state_dict[key.name] = value

        # сохраняем в хранилище словарь с ключами в виде строки
        # (чтобы не сериализовать в хранилище класc перечесления с ключами)
        storage.save(state_dict)

    def load(self, storage: InterfaceStorage) -> None:
        # self.__proxy_dict: Dict = storage.load()
        state_dict: dict = storage.load()

        # Проверка наличия всех ключей в сохранённом ранее словаре
        for key in self.__proxy_dict.keys():
            if key.name not in state_dict:
                # todo отработать штатное завершение приложения в этой ситуации.
                # Ключ отсутствует в сохранённом ранее словаре.
                raise KeyError("Key '{}' absent in loading dict. Mismatch keys in dicts.".format(key))

        # Строковые ключи преобразуются в ключи класса DictKey
        for key, value in state_dict.items():
            try:
                dict_key: DictKey = DictKey[key]
            except KeyError:
                # Такой ключ отсутствует в перечислении DictKey
                # todo отработать штатное завершение приложения в этой ситуации.
                raise KeyError("Key '{}' absent in DictKey enum. Mismatch keys in dicts.".format(key))
            else:
                # Ключ в DictKey есть. Загруженное значение сохраняется в словаре.
                self.__proxy_dict[dict_key] = value

    @property
    def batch_size(self) -> int:
        return self.__proxy_dict[DictKey.BATCH_SIZE]

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        self.__proxy_dict[DictKey.BATCH_SIZE] = value

    @property
    def epoch_start(self) -> int:
        return self.__proxy_dict[DictKey.EPOCH][0]

    @epoch_start.setter
    def epoch_start(self, value: int) -> None:
        self.__proxy_dict[DictKey.EPOCH][0] = value

    @property
    def epoch_current(self) -> int:
        return self.__proxy_dict[DictKey.EPOCH][1]

    @epoch_current.setter
    def epoch_current(self, value: int) -> None:
        self.__proxy_dict[DictKey.EPOCH][1] = value

    @property
    def epoch_stop(self) -> int:
        return self.__proxy_dict[DictKey.EPOCH][2]

    @epoch_stop.setter
    def epoch_stop(self, value: int) -> None:
        self.__proxy_dict[DictKey.EPOCH][2] = value

    # @property
    # def prev_q_max(self) -> float:
    #     return self.__proxy_dict[DictKey.PREV_Q_MAX]
    #
    # @prev_q_max.setter
    # def prev_q_max(self, value) -> None:
    #     self.__proxy_dict[DictKey.PREV_Q_MAX] = value

    @property
    def actor_optim_state(self) -> dict:
        return self.__proxy_dict[DictKey.ACTOR_OPTIMIZER_STATE]

    @actor_optim_state.setter
    def actor_optim_state(self, optim_state: dict) -> None:
        self.__proxy_dict[DictKey.ACTOR_OPTIMIZER_STATE] = optim_state

    @property
    def critic_optim_state(self) -> dict:
        return self.__proxy_dict[DictKey.CRITIC_OPTIMIZER_STATE]

    @critic_optim_state.setter
    def critic_optim_state(self, optim_state: dict) -> None:
        self.__proxy_dict[DictKey.CRITIC_OPTIMIZER_STATE] = optim_state
