""" Реализация состояния. """
from typing import Dict
from nn_iface.ifaces import InterfaceStorage, ProcessStateInterface, DictKey


class State(ProcessStateInterface):
    """ Класс состояния процесса обучения. """
    def __init__(self):
        # Словарь с данными.
        self.__proxy_dict: Dict = {DictKey.BATCH_SIZE: -1,
                                   DictKey.EPOCH: [0, 0, 0],
                                   DictKey.PREV_Q_MAX: 0.,
                                   DictKey.TEMP_FOR_TEST: 0}

    def save(self, storage: InterfaceStorage) -> None:
        self.__proxy_dict[DictKey.TEMP_FOR_TEST] += 1
        # # Полученный объект должен быть потомком класса-нити
        # if not isinstance(storage, StateStorage):
        #     raise TypeError("Input argument is wrong class: {}. It should be a object of StateStorage class".
        #                     format(storage.__class__))

        storage.save(self.__proxy_dict)
        # if not storage.is_alive():
        #     # Если нить ещё не запущена
        #     # Запускаем её
        #     storage.start()
        #     # И отправляем данные на сохранение.
        #     storage.save_queue.put(self.__proxy_dict)
        # else:
        #     # Если нить уже запущена
        #     if not storage.report_queue.empty():
        #         # И если есть сообщение, что завершено предыдущее сохранение
        #         # Забираем элемент из очереди репортов.
        #         storage.report_queue.get()
        #         # Отправляем список состояния на сохранение.
        #         storage.save_queue.put(self.__proxy_dict)
        #     else:
        #         # А если репорта о завершении предыдущего сохранения ещё нет - ничего не сохраняем.
        #         # Пропускаем действие, чтобы не создавать очередь в очереди.
        #         pass

    def load(self, storage: InterfaceStorage) -> None:
        # self.__dict_loaded = True
        self.__proxy_dict: Dict = storage.load()

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

    @property
    def prev_q_max(self) -> float:
        return self.__proxy_dict[DictKey.PREV_Q_MAX]

    @prev_q_max.setter
    def prev_q_max(self, value) -> None:
        self.__proxy_dict[DictKey.PREV_Q_MAX] = value
